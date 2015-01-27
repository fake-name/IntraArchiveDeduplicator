#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging

import random
random.seed()

import psycopg2

import settings

from contextlib import contextmanager

import sql
import sql.aggregate as sqla
import sql.operators as sqlo
import sql.functions as sqlf

import multiprocessing
import functools
import operator as opclass

class DbApi():

	tableName = 'dedupitems'
	QUERY_DEBUG = False

	inLargeTransaction = False


	loggerPath = "Main.DbApi"


	def __init__(self):

		# If we're running as a multiprocessing thread, inject that into
		# the logger path
		threadName = multiprocessing.current_process().name
		if threadName:
			self.log = logging.getLogger("%s.%s" % (self.loggerPath, threadName))
		else:
			self.log = logging.getLogger(self.loggerPath)

		self.connect()

		# self.conn.autocommit = True
		with self.transaction() as cur:

			# print("DB opened.")
			cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", (self.tableName,))
			# print("table exists = ", cur.rowcount)
			tableExists = bool(cur.rowcount)
			if not tableExists:
				self.log.info("Need to create table!")
				cur.execute('''CREATE TABLE IF NOT EXISTS {table} (
													dbId            SERIAL PRIMARY KEY,

													fsPath          text NOT NULL,
													internalPath    text NOT NULL,

													itemHash        text,
													pHash           bigint,
													dHash           bigint,
													itemKind        text,

													imgx            INTEGER,
													imgy            INTEGER,

													scantime        DOUBLE PRECISION DEFAULT 0

													);'''.format(table=self.tableName))

				self.log.info("Creating indexes")
				cur.execute('''CREATE UNIQUE INDEX {table}_name_index     ON {table}(fsPath, internalPath);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_path_index     ON {table}(fsPath text_pattern_ops);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_ihash_index    ON {table}(itemHash);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_phash_index    ON {table}(pHash);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_dhash_index    ON {table}(dHash);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_scantime_index ON {table}(scantime);'''.format(table=self.tableName))
				self.log.info("Done!")

				# CREATE        INDEX dedupitems_scantime_index ON dedupitems(scantime)

		self.table = sql.Table(self.tableName.lower())

		self.cols = (
				self.table.dbid,
				self.table.fspath,
				self.table.internalpath,
				self.table.itemhash,
				self.table.phash,
				self.table.dhash,
				self.table.itemkind,
				self.table.imgx,
				self.table.imgy,

				# self.table.phash_text,
				# self.table.dhash_text
			)


		self.colMap = {
				"dbid"          : self.table.dbid,
				"fspath"        : self.table.fspath,
				"internalpath"  : self.table.internalpath,
				"itemhash"      : self.table.itemhash,
				"phash"         : self.table.phash,
				"dhash"         : self.table.dhash,
				"itemkind"      : self.table.itemkind,
				"imgx"          : self.table.imgx,
				"imgy"          : self.table.imgy,


				# "phash_text"    : self.table.phash_text,
				# "dhash_text"    : self.table.dhash_text

			}



	def connect(self):


		try:
			# hook up login creds (overridden for tests)
			self._psqlDbIpAddr = settings.PSQL_IP
			self._psqlDbName   = settings.PSQL_DB_NAME
			self._psqlUserName = settings.PSQL_USER
			self._psqlUserPass = settings.PSQL_PASS
		except:
			print("WARNING: DB Credentials not available. Is this a test environment?")

		try:
			self.conn = psycopg2.connect(dbname  = self._psqlDbName,
										user     = self._psqlUserName,
										password = self._psqlUserPass)

		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host    = self._psqlDbIpAddr,
										dbname   = self._psqlDbName,
										user     = self._psqlUserName,
										password = self._psqlUserPass)

	def close(self):
		self.conn.close()

	@contextmanager
	def transaction(self, commit=True):
		cursor = self.conn.cursor()

		# Larger transaction blocks need to auto-skip
		# local commit operations
		if self.inLargeTransaction:
			commit=False

		if commit:
			cursor.execute("BEGIN;")

		try:
			yield cursor

		except Exception as e:
			if commit:
				cursor.execute("ROLLBACK;")
			raise e

		finally:
			if commit:
				cursor.execute("COMMIT;")

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Generic SQL tooling
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def keyToCol(self, key):
		key = key.lower()
		if not key in self.colMap:
			raise ValueError("Invalid column name '%s'" % key)
		return self.colMap[key]

	def keysToCols(self, inKeyList):
		cols = []
		for colName in inKeyList:
			cols.append(self.keyToCol(colName))
		return cols

	def sqlBuildInsertArgs(self, **kwargs):

		cols = []
		vals = []

		for key, val in kwargs.items():
			cols.append(self.keyToCol(key))
			vals.append(val)

		query = self.table.insert(columns=cols, values=[vals])

		query, params = tuple(query)

		return query, params

	def sqlBuildConditional(self, **kwargs):
		operators = []

		# Short circuit and return none (so the resulting where clause is all items) if no kwargs are passed.
		if not kwargs:
			return None

		for key, val in kwargs.items():
			operators.append((self.keyToCol(key) == val))

		# This is ugly as hell, but it functionally returns x & y & z ... for an array of [x, y, z]
		# And allows variable length arrays.
		conditional = functools.reduce(opclass.and_, operators)
		return conditional


	#TODO: Add unit tests!
	def upsert(self, *args, **kwargs):
		try:
			self.insertIntoDb(*args, **kwargs)
		except psycopg2.IntegrityError:
			self.updateDbEntry(*args, **kwargs)

	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		query, queryArguments = self.sqlBuildInsertArgs(**kwargs)

		self.log.debug("Query = '%s'", query)
		self.log.debug("Args = '%s'", queryArguments)

		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)



	def generateUpdateQuery(self, where=False, **kwargs):
		if 'fspath' in kwargs or 'internalpath' in kwargs or 'dbid' in kwargs:
			raise ValueError("Cannot generate correct update query with lowercase params!")
		if not where:
			if "dbId" in kwargs:
				where = (self.table.dbid == kwargs.pop('dbId'))
			elif "fsPath" in kwargs and "internalPath" in kwargs:
				where = (self.table.fspath == kwargs.pop('fsPath')) & (self.table.internalpath == kwargs.pop('internalPath'))
			elif "fsPath" in kwargs:
				where = (self.table.fspath == kwargs.pop('fsPath'))
			else:
				self.log.error("Passed kwargs = '%s'", kwargs)
				raise ValueError("updateDbEntryKey must be passed a single unique column identifier (either dbId, fsPath, or fsPath & internalPath)")

		cols = []
		vals = []

		for key, val in kwargs.items():
			cols.append(self.keyToCol(key))
			vals.append(val)

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)
		return query, params


	def updateDbEntry(self, commit=True, **kwargs):

		query, queryArguments = self.generateUpdateQuery(**kwargs)


		self.log.debug("Query = '%s'", query)
		self.log.debug("Args = '%s'", queryArguments)


		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)



	def getItems(self, wantCols=None, where=None, **kwargs):
		cols = []
		if wantCols:
			cols = self.keysToCols(wantCols)
		else:
			cols = self.cols

		if not where:
			where = self.sqlBuildConditional(**kwargs)

		query = self.table.select(*cols, where=where)

		query, params = tuple(query)

		self.log.debug("Query = '%s'", query)
		self.log.debug("Args = '%s'", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchall()

		return ret

	def getItem(self, **kwargs):
		ret = self.getItems(**kwargs)


		# print("Getitem Kwargs:")
		# print(kwargs)
		# print("Returning:")
		# print(ret)
		# print()

		if len(ret) > 1:
			raise ValueError("GetItem can only fetch a single item.")

		if ret:
			return ret[0]
		return ret

	def getStreamingCursor(self, wantCols=None, where=None, limit=None, **kwargs):
		cols = []
		if wantCols:
			for colName in wantCols:
				cols.append(self.keyToCol(colName))
		else:
			cols = self.cols

		if not where:
			where = self.sqlBuildConditional(**kwargs)


		query = self.table.select(*cols, where=where)

		if limit:
			query.limit = int(limit)

		query, params = tuple(query)


		self.log.debug("Query = '%s'", query)
		self.log.debug("Args = '%s'", params)

		# Specifying a name for the cursor causes it to run server-side, making is stream results,
		# rather then completing the query and returning them as a lump item (which blocks)

		self.conn.cursor().execute("BEGIN;")
		cur = self.conn.cursor("streaming_cursor")
		cur.execute(query, params)
		return cur


	def getNumberOfRows(self, where=None, **kwargs):
		if not where:
			where = self.sqlBuildConditional(**kwargs)

		query = self.table.select(sqla.Count(sql.Literal(1)), where=where)

		query, params = tuple(query)


		self.log.debug("Query = '%s'", query)
		self.log.debug("Args = '%s'", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchone()

		return ret[0]

	def getNumberOfPhashes(self, **kwargs):
		where = self.sqlBuildConditional(**kwargs)
		havePHash = (self.keyToCol('pHash') != None)

		if where:
			where = where & havePHash
		else:
			where = havePHash

		return self.getNumberOfRows(where=where)

	def itemInDB(self, **kwargs):
		return bool(self.getNumberOfRows(**kwargs))


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# More complex queries
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def getDuplicateImages(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT DISTINCT(fsPath)
						FROM {table}
						WHERE itemHash IN
						(
							SELECT itemHash
							FROM {table}
							WHERE fsPath LIKE %s
							GROUP BY itemHash
							HAVING COUNT(*) > 1
						)'''.format(table=self.tableName), (basePath+"%", ))
		ret = cur.fetchall()
		self.conn.commit()
		return [item[0] for item in ret]

	def getDuplicateBaseFiles(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT fsPath, itemHash
						FROM {table}
						WHERE itemHash IN
						(
							SELECT itemHash
							FROM {table}
							WHERE internalPath=%s
							GROUP BY itemHash
							HAVING COUNT(*) > 1
						)
						AND internalPath=%s
						AND fsPath LIKE %s'''.format(table=self.tableName), ("", "", basePath+"%"))

		ret = cur.fetchall()
		self.conn.commit()
		ret = [(item[0], item[1]) for item in ret]
		return set(ret)

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Old-shit compatibility wrappings and convenience calls
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def basePathInDB(self, basePath):
		return self.itemInDB(fsPath=basePath)

	def numHashInDB(self, itemHash):
		return self.itemInDB(itemHash=itemHash)

	def getById(self, dbId, wantCols=None):
		if not wantCols:
			wantCols = ["fsPath","internalPath","itemHash"]
		return self.getItems(wantCols=wantCols, dbId=dbId)

	def getByHash(self, itemHash, wantCols=None):
		if not wantCols:
			wantCols = ["fsPath","internalPath","itemHash"]
		return self.getItems(wantCols=wantCols, itemHash=itemHash)

	def getOtherHashes(self, itemHash, fsMaskPath, wantCols=None):
		if not wantCols:
			wantCols = ["fsPath","internalPath","itemHash"]
		where = (self.table.itemhash == itemHash) & (self.table.fspath != fsMaskPath)
		return self.getItems(wantCols, where=where)



	# Update items


	def moveItem(self, oldPath, newPath):
		where = (self.table.fspath == oldPath)
		self.updateDbEntry(where=where, fsPath=newPath)


	def getPhashLikeBasePath(self, basePath):
		where = (sqlo.Like(self.table.fspath, basePath+'%')) & (self.table.phash != None)
		return self.getItems(wantCols=["dbId","pHash"], where=where)

	def getPHashes(self, limit=None):
		where = (self.table.phash != None)
		return self.getStreamingCursor(["dbId", "pHash"], where=where, limit=limit)

	def getLike(self, likeCol, colVal, wantCols=None):
		where = (sqlo.Like(self.keyToCol(likeCol), colVal+'%'))
		return self.getItems(wantCols=wantCols, where=where)


	def getLikeBasePath(self, basePath):
		wantCols = [
			"fspath",
			"internalpath",
			"itemhash",
			"phash",
			"dhash",
			"imgx",
			"imgy"
		]
		return self.getLike('fsPath', basePath, wantCols=wantCols)


	def getFileDictLikeBasePath(self, basePath):
		wantCols = [
			"dbId",
			"fsPath",
			"internalPath",
			"itemHash",
			"pHash",
			"dHash",
			"imgx",
			"imgy"
		]

		items = self.getLike('fsPath', basePath, wantCols=wantCols)

		ret = {}
		for item in items:
			item = dict(zip(wantCols, item))

			if item["fsPath"] in ret:
				ret[item["fsPath"]].append(item)
			else:
				ret[item["fsPath"]] = [item]

		return ret


	def deleteDbRows(self, commit=True, where=None, **kwargs):

		if not where:
			where = self.sqlBuildConditional(**kwargs)

		if not where:
			raise ValueError("Trying to delete the whole table?")

		query = self.table.delete(where=where)

		query, params = tuple(query)

		self.log.info("Query = '%s'", query)
		self.log.info("Args = '%s'", params)


		with self.transaction() as cur:
			cur.execute(query, params)


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Block-transaction methods
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def commit(self):
		cur = self.conn.cursor()
		cur.execute("COMMIT;")
		self.inLargeTransaction = False
		self.log.info("Block complete. Committing changes to DB.")

	def rollback(self):
		cur = self.conn.cursor()
		cur.execute("ROLLBACK;")
		self.inLargeTransaction = False
		self.log.warning("Block failed. Rolling back changes to DB.")

	def begin(self):
		self.log.info("Beginning block transaction.")
		self.inLargeTransaction = True
		cur = self.conn.cursor()
		cur.execute("BEGIN;")

	def insertItem(self, *args, **kwargs):
		if args:
			raise ValueError("All values passed to insertItem must be keyworded. Passed positional arguments: '%s'" % args)
		print("FIX ME INDIRECT CALL TWO!!!!")
		self.insertIntoDb(**kwargs)


	def updateItem(self, basePath, internalPath, **kwargs):
		print("FIX ME INDIRECT CALL ONE!!!!")
		self.updateDbEntry(fsPath=basePath, internalPath=internalPath, **kwargs)


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# TODO: Clean up everything from here down
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



	def getDHashes(self, limit=None):

		# Specifying a name for the cursor causes it to run server-side, making is stream results,
		# rather then completing the query and returning them as a lump item (which blocks)
		cur = self.conn.cursor("hash_fetcher")
		if not limit:
			cur.execute("SELECT dbId, dHash FROM {table} WHERE dHash IS NOT NULL;".format(table=self.tableName))
		else:
			limit = int(limit)
			cur.execute("SELECT dbId, dHash FROM {table} WHERE dHash IS NOT NULL LIMIT %s;".format(table=self.tableName), (limit, ))

		return cur


	def deleteLikeBasePath(self, basePath):
		self.log.info("Deleting all items with base-path '%s'", basePath)
		cur = self.conn.cursor()
		cur.execute("DELETE FROM {table} WHERE fsPath LIKE %s;".format(table=self.tableName), (basePath+"%", ))
		if cur.rowcount == 0:
			self.log.warning("Deleted {num} items!".format(num=cur.rowcount))
		else:
			self.log.info("Deleted {num} items on path '{path}'!".format(num=cur.rowcount, path=basePath))
		self.conn.commit()


	def deleteBasePath(self, basePath):
		with self.transaction() as cur:
			cur.execute("DELETE FROM {table} WHERE fsPath=%s;".format(table=self.tableName), (basePath, ))
			if cur.rowcount == 0:
				pass
			else:
				self.log.info("Deleted {num} items on path '{path}'!".format(num=cur.rowcount, path=basePath))

	def getItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash,pHash,imgx,imgy,dbId FROM {table} WHERE fsPath=%s;".format(table=self.tableName), (basePath, ))

		rows = cur.fetchall()
		self.conn.commit()

		ret = []
		cols = ['fsPath','internalPath','itemhash','pHash','imgx','imgy','dbId']
		for row in rows:
			ret.append(dict(zip(cols, row)))
		return ret

	def getItemsOnBasePathInternalPath(self, basePath, internalPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash,pHash,imgx,imgy,dbId FROM {table} WHERE fsPath=%s AND internalPath=%s;".format(table=self.tableName), (basePath, internalPath))

		rows = cur.fetchall()
		self.conn.commit()

		ret = []
		cols = ['fsPath','internalPath','itemhash','pHash','imgx','imgy','dbId']
		for row in rows:
			ret.append(dict(zip(cols, row)))
		return ret

		return ret

	def getItemNumberOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM {table} WHERE fsPath=%s;".format(table=self.tableName), (basePath, ))

		ret = cur.fetchone()
		self.conn.commit()
		return ret[0]

	def getInternalItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM {table} WHERE fsPath=%s AND internalPath IS NOT NULL;".format(table=self.tableName), (basePath, ))
		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getUniqueOnBasePath(self, basePath):

		cur = self.conn.cursor()
		cur.execute("SELECT DISTINCT(fsPath) FROM {table} WHERE fsPath LIKE %s;".format(table=self.tableName), (basePath+"%", ))

		return cur

	def getAllItems(self):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath, internalPath, itemHash FROM {table};".format(table=self.tableName))
		return cur

	def getItemNum(self):
		cur = self.conn.cursor()
		cur.execute("SELECT count(*) FROM {table};".format(table=self.tableName))
		ret = cur.fetchone()
		self.conn.commit()
		return ret

	def getHashes(self, fsPath, internalPath):

		cur = self.conn.cursor()
		cur.execute("SELECT itemHash,pHash,dHash FROM {table} WHERE fsPath=%s AND internalPath=%s;".format(table=self.tableName), (fsPath, internalPath))
		ret = cur.fetchone()

		self.conn.commit()
		if ret:
			return ret
		return False, False, False


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Oddball utilities primarily for testing
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	def getIdExtents(self):

		query = self.table.select(sqla.Min(self.keyToCol('dbId')), sqla.Max(self.keyToCol('dbId')))

		query, params = tuple(query)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchone()

		# print("IdExtents = ", ret)
		return ret



	def getRandomRow(self):
		wantCols = [
			"fspath",
			"internalpath",
			"itemhash",
			"phash",
			"dhash",
			"imgx",
			"imgy"
		]
		cols = self.keysToCols(wantCols)

		minId, maxId = self.getIdExtents()



		ret = None
		attempts = 0
		while not ret:
			attempts += 1
			if attempts > 10:
				raise ValueError("Could not fetch random item?")
			dbId = random.randint(minId, maxId+1)
			query = self.table.select(*cols, where=(self.keyToCol('dbId') == dbId))

			query, params = tuple(query)
			with self.transaction() as cur:
				cur.execute(query, params)
				ret = cur.fetchone()


		return ret

def test():
	ind = DbApi()


if __name__ == "__main__":

	import scanner.logSetup
	scanner.logSetup.initLogging()
	test()

