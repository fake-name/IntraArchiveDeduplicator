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



		self.conn = psycopg2.connect(host=settings.PSQL_IP,
									dbname=settings.PSQL_DB_NAME,
									user=settings.PSQL_USER,
									password=settings.PSQL_PASS)
		# self.conn.autocommit = True
		with self.transaction() as cur:

			# print("DB opened.")
			cur.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", ('dedupitems',))
			# print("table exists = ", cur.rowcount)
			tableExists = bool(cur.rowcount)
			if not tableExists:
				cur.execute('''CREATE TABLE IF NOT EXISTS dedupitems (
													dbId            SERIAL PRIMARY KEY,

													fsPath          text NOT NULL,
													internalPath    text NOT NULL,

													itemHash        text,
													pHash           text,
													dHash           text,
													itemKind        text,

													imgx            INTEGER,
													imgy            INTEGER

													);''')

				print("Checking indexes exist")
				cur.execute('''CREATE UNIQUE INDEX name_index  ON dedupitems(fsPath, internalPath);''')
				cur.execute('''CREATE        INDEX path_index  ON dedupitems(fsPath text_pattern_ops);''')
				cur.execute('''CREATE        INDEX ihash_index ON dedupitems(itemHash);''')
				cur.execute('''CREATE        INDEX phash_index ON dedupitems(pHash);''')
				cur.execute('''CREATE        INDEX dhash_index ON dedupitems(dHash);''')


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

	def sqlBuildInsertArgs(self, **kwargs):

		cols = []
		vals = []

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.insert(columns=cols, values=[vals])

		query, params = tuple(query)

		return query, params

	def sqlBuildConditional(self, **kwargs):
		operators = []

		for key, val in kwargs.items():
			key = key.lower()
			operators.append((self.colMap[key] == val))

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
			key = key.lower()
			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
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
				cols.append(self.colMap[colName.lower()])
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
				cols.append(self.colMap[colName])
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

	def itemInDB(self, **kwargs):
		where = self.sqlBuildConditional(**kwargs)
		query = self.table.select(sqla.Count(sql.Literal(1)), where=where)

		query, params = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", params)


		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchone()

		return ret


	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# More complex queries
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def getDuplicatePhashes(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT pHash, dHash, dbId, fsPath, internalPath
						FROM dedupitems
						WHERE pHash IN
						(
							SELECT pHash
							FROM dedupitems
							WHERE fsPath LIKE %s
							GROUP BY pHash
							HAVING COUNT(*) > 1
						)
						ORDER BY pHash''', (basePath+"%", ))
		ret = cur.fetchall()
		self.conn.commit()
		return ret


	def getDuplicateImages(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT DISTINCT(fsPath)
						FROM dedupitems
						WHERE itemHash IN
						(
							SELECT itemHash
							FROM dedupitems
							WHERE fsPath LIKE %s
							GROUP BY itemHash
							HAVING COUNT(*) > 1
						)''', (basePath+"%", ))
		ret = cur.fetchall()
		self.conn.commit()
		return [item[0] for item in ret]

	def getDuplicateBaseFiles(self, basePath):
		cur = self.conn.cursor()

		cur.execute(''' SELECT fsPath, itemHash
						FROM dedupitems
						WHERE itemHash IN
						(
							SELECT itemHash
							FROM dedupitems
							WHERE internalPath=%s
							GROUP BY itemHash
							HAVING COUNT(*) > 1
						)
						AND internalPath=%s
						AND fsPath LIKE %s''', ("", "", basePath+"%"))

		ret = cur.fetchall()
		self.conn.commit()
		print("Ret = ", ret[0])
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


	def getLikeBasePath(self, basePath):
		where = (sqlo.Like(self.table.fspath, basePath+'%'))
		wantCols = [
			"fspath",
			"internalpath",
			"itemhash",
			"phash",
			"dhash",
			"imgx",
			"imgy"
		]
		return self.getItems(wantCols=wantCols, where=where)


	def getFileDictLikeBasePath(self, basePath):
		items = self.getLikeBasePath(basePath)

		ret = {}
		for fsPath, internalPath, itemHash, pHash, dHash, imgx, imgy in items:
			item = {
				"fsPath"       : fsPath,
				"internalPath" : internalPath,
				"itemHash"     : itemHash,
				"pHash"        : pHash,
				"dHash"        : dHash,
				"imgx"         : imgx,
				"imgy"         : imgy
			}
			if fsPath in ret:
				ret[fsPath].append(item)
			else:
				ret[fsPath] = [item]

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
			raise ValueError("All values passed to inseetItem must be keyworded. Passed positional arguments: '%s'" % args)
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
			cur.execute("SELECT dbId, dHash FROM dedupitems WHERE dHash IS NOT NULL;")
		else:
			limit = int(limit)
			cur.execute("SELECT dbId, dHash FROM dedupitems WHERE dHash IS NOT NULL LIMIT %s;", (limit, ))

		return cur



	# TODO: Refactor to use kwargs
	def updateItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None, imgX=None, imgY=None):
		cur = self.conn.cursor()
		cur.execute("UPDATE dedupitems SET itemhash=%s, pHash=%s, dHash=%s, imgx=%s, imgy=%s WHERE fsPath=%s AND internalPath=%s;",
			(itemHash, pHash, dHash, imgX, imgY, basePath, internalPath))


	def deleteLikeBasePath(self, basePath):
		self.log.info("Deleting all items with base-path '%s'", basePath)
		cur = self.conn.cursor()
		cur.execute("DELETE FROM dedupitems WHERE fsPath LIKE %s;", (basePath+"%", ))
		if cur.rowcount == 0:
			self.log.warn("Deleted {num} items!".format(num=cur.rowcount))
		else:
			self.log.info("Deleted {num} items on path '{path}'!".format(num=cur.rowcount, path=basePath))
		self.conn.commit()


	def deleteBasePath(self, basePath):
		with self.transaction() as cur:
			cur.execute("DELETE FROM dedupitems WHERE fsPath=%s;", (basePath, ))
			if cur.rowcount == 0:
				pass
			else:
				self.log.info("Deleted {num} items on path '{path}'!".format(num=cur.rowcount, path=basePath))

	def getItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash,pHash,dbId FROM dedupitems WHERE fsPath=%s;", (basePath, ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getItemsOnBasePathInternalPath(self, basePath, internalPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath=%s AND internalPath=%s;", (basePath, internalPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getItemNumberOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s;", (basePath, ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getInternalItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath=%s AND internalPath IS NOT NULL;", (basePath, ))
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
		cur.execute("INSERT INTO dedupitems (fsPath, internalPath, itemhash) VALUES %s;" % ",".join(self.insertStr), self.insertList)

		self.conn.commit()
		self.insertStr = []
		self.insertList = []


	def getUniqueOnBasePath(self, basePath):

		cur = self.conn.cursor()
		cur.execute("SELECT DISTINCT(fsPath) FROM dedupitems WHERE fsPath LIKE %s;", (basePath+"%", ))

		return cur




	def getAllItems(self):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath, internalPath, itemHash FROM dedupitems;")
		return cur

	def getItemNum(self):
		cur = self.conn.cursor()
		cur.execute("SELECT count(*) FROM dedupitems;")
		ret = cur.fetchone()
		self.conn.commit()
		return ret

	def getHashes(self, fsPath, internalPath):

		cur = self.conn.cursor()
		cur.execute("SELECT itemHash,pHash,dHash FROM dedupitems WHERE fsPath=%s AND internalPath=%s;", (fsPath, internalPath))
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

