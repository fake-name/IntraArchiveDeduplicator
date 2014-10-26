#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging

import random
random.seed()

import psycopg2
import logSetup

import settings

from contextlib import contextmanager

import sql
import sql.aggregate as sqla
import sql.operators as sqlo

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



		try:
			self.conn = psycopg2.connect(dbname=settings.PSQL_DB_NAME,
										user=settings.PSQL_USER,
										password=settings.PSQL_PASS)

		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host=settings.PSQL_IP,
										dbname=settings.PSQL_DB_NAME,
										user=settings.PSQL_USER,
										password=settings.PSQL_PASS)
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
													pHash           text,
													dHash           text,
													itemKind        text,

													imgx            INTEGER,
													imgy            INTEGER

													);'''.format(table=self.tableName))

				self.log.info("Checking indexes exist")
				cur.execute('''CREATE UNIQUE INDEX {table}_name_index  ON {table}(fsPath, internalPath);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_path_index  ON {table}(fsPath text_pattern_ops);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_ihash_index ON {table}(itemHash);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_phash_index ON {table}(pHash);'''.format(table=self.tableName))
				cur.execute('''CREATE        INDEX {table}_dhash_index ON {table}(dHash);'''.format(table=self.tableName))


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
				self.table.imgy
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
				"imgy"          : self.table.imgy
			}




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

	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		query, queryArguments = self.sqlBuildInsertArgs(**kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)



	def generateUpdateQuery(self, where=False, **kwargs):
		if not where:
			if "dbId" in kwargs:
				where = (self.table.dbid == kwargs.pop('dbId'))
			elif "fsPath" in kwargs and "internalPath" in kwargs:
				where = (self.table.fsPath == kwargs.pop('fsPath')) & (self.table.internalPath == kwargs.pop('internalPath'))
			elif "fsPath" in kwargs:
				where = (self.table.fsPath == kwargs.pop('fsPath'))
			else:
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

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)


		with self.transaction(commit=commit) as cur:
			cur.execute(query, queryArguments)


	def getItems(self, wantCols=None, where=None, **kwargs):
		cols = []
		if wantCols:
			for colName in wantCols:
				cols.append(self.keyToCol(colName))
		else:
			cols = self.cols

		if not where:
			where = self.sqlBuildConditional(**kwargs)



		query = self.table.select(*cols, where=where)


		query, params = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchall()

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

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", params)

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

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchone()

		return ret[0]

	def getNumberOfPhashes(self, **kwargs):
		where = self.sqlBuildConditional(**kwargs)
		where = where & (self.keyToCol('pHash') != '')
		return self.getNumberOfRows(where=where)

	def itemInDB(self, **kwargs):
		return bool(self.getNumberOfRows(**kwargs))


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# More complex queries
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def getDuplicatePhashes(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT pHash, dHash, dbId, fsPath, internalPath
						FROM {table}
						WHERE pHash IN
						(
							SELECT pHash
							FROM {table}
							WHERE fsPath LIKE %s AND
							pHash != ''
							GROUP BY pHash
							HAVING COUNT(*) > 1
						)
						ORDER BY pHash'''.format(table=self.tableName), (basePath+"%", ))
		ret = cur.fetchall()
		self.conn.commit()
		return ret


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

	def getByHash(self, itemHash):
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], itemHash=itemHash)

	def getById(self, dbId):
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], dbId=dbId)

	def getOtherHashes(self, itemHash, fsMaskPath):
		where = (self.table.itemhash == itemHash) & (self.table.fspath != fsMaskPath)
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], where=where)

	def getOtherDPHashes(self, dHash, pHash, fsMaskPath):
		where = ((self.table.dhash == dHash) & (self.table.phash == pHash)) & (self.table.fspath != fsMaskPath)
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], where=where)

	def getOtherDHashes(self, dHash, fsMaskPath):
		where = ((self.table.dhash == dHash)) & (self.table.fspath != fsMaskPath)
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], where=where)

	def getOtherPHashes(self, pHash, fsMaskPath):
		where = ((self.table.phash == pHash)) & (self.table.fspath != fsMaskPath)
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], where=where)



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
		self.log.warn("Block failed. Rolling back changes to DB.")

	def begin(self):
		self.log.info("Beginning block transaction.")
		self.inLargeTransaction = True
		cur = self.conn.cursor()
		cur.execute("BEGIN;")

	def insertItem(self, *args, **kwargs):
		if args:
			raise ValueError("All values passed to insertItem must be keyworded. Passed positional arguments: '%s'" % args)
		print("FIX ME INDIRECT CALL!!!!")
		self.insertIntoDb(**kwargs)


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



	# TODO: Refactor to use kwargs
	def updateItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None, imgX=None, imgY=None):
		cur = self.conn.cursor()
		cur.execute("UPDATE {table} SET itemhash=%s, pHash=%s, dHash=%s, imgx=%s, imgy=%s WHERE fsPath=%s AND internalPath=%s;".format(table=self.tableName),
			(itemHash, pHash, dHash, imgX, imgY, basePath, internalPath))


	def deleteLikeBasePath(self, basePath):
		self.log.info("Deleting all items with base-path '%s'", basePath)
		cur = self.conn.cursor()
		cur.execute("DELETE FROM {table} WHERE fsPath LIKE %s;".format(table=self.tableName), (basePath+"%", ))
		if cur.rowcount == 0:
			self.log.warn("Deleted {num} items!".format(num=cur.rowcount))
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
		cur.execute("SELECT fsPath,internalPath,itemhash,pHash,dbId FROM {table} WHERE fsPath=%s;".format(table=self.tableName), (basePath, ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getItemsOnBasePathInternalPath(self, basePath, internalPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM {table} WHERE fsPath=%s AND internalPath=%s;".format(table=self.tableName), (basePath, internalPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getItemNumberOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM {table} WHERE fsPath=%s;".format(table=self.tableName), (basePath, ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getInternalItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM {table} WHERE fsPath=%s AND internalPath IS NOT NULL;".format(table=self.tableName), (basePath, ))
		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def aggregateItems(self, basePath, internalPath, itemHash):
		if not hasattr(self, "insertStr"):
			self.insertStr = []
		if not hasattr(self, "insertList"):
			self.insertList = []

		self.insertStr.append("(%s,%s,%s)")
		self.insertList.append(basePath)
		self.insertList.append(internalPath)
		self.insertList.append(itemHash)


	def insertAggregate(self):
		cur = self.conn.cursor()
		cur.execute("INSERT INTO {table} (fsPath, internalPath, itemhash) VALUES {vals};".format(table=self.tableName, vals=",".join(self.insertStr)), self.insertList)

		self.conn.commit()
		self.insertStr = []
		self.insertList = []


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


def test():
	ind = DbApi()
	ind.QUERY_DEBUG = True
	cond = ind.getPHashes(limit=200)

if __name__ == "__main__":

	logSetup.initLogging()
	test()

