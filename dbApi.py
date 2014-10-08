#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging

import random
random.seed()

import psycopg2
import logSetup

import settings

class DbApi():

	def __init__(self):

		self.log = logging.getLogger("Main.DbApi")



		self.conn = psycopg2.connect(host=settings.PSQL_IP,
									dbname=settings.PSQL_DB_NAME,
									user=settings.PSQL_USER,
									password=settings.PSQL_PASS)
		# self.conn.autocommit = True
		with self.conn.cursor() as cur:

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

			# print("Indexes Instantiated")
		# else:
		# 	print("Table exists")

		self.conn.commit()

	# General TODO:
	# Use python-sql to allow flexible kwargs for queries. This
	# should allow the number of discrete methods here to be cut DRAMATICALLY.

	def rollback(self):
		self.log.info("Rolling back DB changes.")
		cur = self.conn.cursor()
		cur.execute("ROLLBACK;")

	def commit(self):
		self.log.info("Committing changes to DB.")
		self.conn.commit()

	def itemInDB(self, basePath, internalPath, itemHash):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s AND internalPath=%s AND itemHash=%s;", (basePath, internalPath, itemHash))
		ret = cur.fetchone()
		self.conn.commit()
		return ret

	def basePathInDB(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		ret = cur.fetchone()
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


	def numHashInDB(self, itemHash):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE itemHash=%s;", (itemHash, ))

		ret = cur.fetchone()
		self.conn.commit()
		return ret


	def getByHash(self, itemHash):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE itemHash=%s;", (itemHash, ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

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

	def moveItem(self, oldPath, newPath):
		cur = self.conn.cursor()
		cur.execute("UPDATE dedupitems SET fsPath=%s WHERE fsPath=%s;", (newPath, oldPath))

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
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath LIKE %s;", (basePath+"%", ))

		ret = cur.fetchall()
		self.conn.commit()
		return ret

	def deleteBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("DELETE FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		if cur.rowcount == 0:
			pass
		else:
			self.log.info("Deleted {num} items!".format(num=cur.rowcount))
		self.conn.commit()

	def getItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath=%s;", (basePath, ))

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


if __name__ == "__main__":

	logSetup.initLogging()
	ind = DbInterface()


