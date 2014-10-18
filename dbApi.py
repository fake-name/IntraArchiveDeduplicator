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

import copy
import functools
import operator as opclass

class DbApi():

	tableName = 'dedupitems'
	QUERY_DEBUG = True

	def __init__(self):

		self.log = logging.getLogger("Main.DbApi")



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
				"dbId"          : self.table.dbid,
				"fsPath"        : self.table.fspath,
				"internalPath"  : self.table.internalpath,
				"itemHash"      : self.table.itemhash,
				"pHash"         : self.table.phash,
				"dHash"         : self.table.dhash,
				"itemKind"      : self.table.itemkind,
				"imgx"          : self.table.imgx,
				"imgy"          : self.table.imgy
			}



	@contextmanager
	def transaction(self, commit=True):
		cursor = self.conn.cursor()
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
			print(key, val)
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



	def generateUpdateQuery(self, **kwargs):
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


	def getItems(self, wantCols=None, **kwargs):
		cols = []
		if wantCols:
			for colName in wantCols:
				cols.append(self.colMap[colName])
		else:
			cols = self.cols

		where = self.sqlBuildConditional(**kwargs)
		query = self.table.select(*cols, where=where)


		query, params = tuple(query)

		with self.transaction() as cur:
			cur.execute(query, params)
			ret = cur.fetchall()

		return ret

	def itemInDB(self, **kwargs):
		where = self.sqlBuildConditional(**kwargs)
		query = self.table.select(sqla.Count(sql.Literal(1)), where=where)

		query, params = tuple(query)

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
	# Old-shit compatibility wrappings
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


	def basePathInDB(self, basePath):
		return self.itemInDB(fsPath=basePath)

	def numHashInDB(self, itemHash):
		return self.itemInDB(itemHash=itemHash)

	def getByHash(self, itemHash):
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], itemHash=itemHash)

	def getById(self, dbId):
		return self.getItems(wantCols=["fsPath","internalPath","itemHash"], dbId=dbId)



	# Update items

	def moveItem(self, oldPath, newPath):
		self.updateDbEntry()
		with self.transaction() as cur:
			cur.execute("UPDATE dedupitems SET fsPath=%s WHERE fsPath=%s;", (newPath, oldPath))




	def commit(self):
		print("FIXME")
		print("FIXME")
		print("FIXME")
		print("FIXME")
		print("FIXME")
		print("FIXME")

		self.log.info("Committing changes to DB.")
		self.conn.commit()


	def getPhashLikeBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT dbId, pHash FROM dedupitems WHERE fsPath LIKE %s AND pHash IS NOT NULL;", (basePath+"%", ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getPHashes(self, limit=None):

		# Specifying a name for the cursor causes it to run server-side, making is stream results,
		# rather then completing the query and returning them as a lump item (which blocks)
		cur = self.conn.cursor("hash_fetcher")
		if not limit:
			cur.execute("SELECT dbId, pHash FROM dedupitems WHERE pHash IS NOT NULL;")
		else:
			limit = int(limit)
			cur.execute("SELECT dbId, pHash FROM dedupitems WHERE pHash IS NOT NULL LIMIT %s;", (limit, ))

		return cur

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




	def getOtherHashes(self, itemHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE itemHash=%s AND NOT fsPath=%s;", (itemHash, fsMaskPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getOtherDPHashes(self, dHash, pHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE dHash=%s AND pHash=%s AND NOT fsPath=%s;", (dHash, pHash, fsMaskPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getOtherDHashes(self, dHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE dHash=%s AND NOT fsPath=%s;", (dHash, fsMaskPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def getOtherPHashes(self, pHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE pHash=%s AND NOT fsPath=%s;", (pHash, fsMaskPath))

		ret = cur.fetchall()
		self.conn.commit()
		return ret


	# TODO: Refactor to use kwargs
	def insertItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None, imgX=None, imgY=None):
		cur = self.conn.cursor()
		cur.execute("INSERT INTO dedupitems (fsPath, internalPath, itemhash, pHash, dHash, imgx, imgy) VALUES (%s, %s, %s, %s, %s, %s, %s);",
			(basePath, internalPath, itemHash, pHash, dHash, imgX, imgY))


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
			self.log.info("Deleted {num} items!".format(num=cur.rowcount))
		self.conn.commit()

	def getLikeBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash,pHash,dHash,imgx,imgy FROM dedupitems WHERE fsPath LIKE %s;", (basePath+"%", ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def deleteBasePath(self, basePath):
		with self.transaction() as cur:
			cur.execute("DELETE FROM dedupitems WHERE fsPath=%s;", (basePath, ))
			if cur.rowcount == 0:
				pass
			else:
				self.log.info("Deleted {num} items!".format(num=cur.rowcount))

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

	cond = ind.getByHash('500')

if __name__ == "__main__":

	logSetup.initLogging()
	test()

