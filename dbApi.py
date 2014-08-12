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

		self.log = logging.getLogger("Main.Database")



		self.conn = psycopg2.connect(host=settings.PSQL_IP,
									dbname=settings.PSQL_DB_NAME,
									user=settings.PSQL_USER,
									password=settings.PSQL_PASS)
		cur = self.conn.cursor()

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
												itemKind        text

												);''')

			print("Checking indexes exist")
			cur.execute('''CREATE UNIQUE INDEX name_index  ON dedupitems(fsPath, internalPath);''')
			cur.execute('''CREATE        INDEX ihash_index ON dedupitems(itemHash);''')
			cur.execute('''CREATE        INDEX phash_index ON dedupitems(pHash);''')
			cur.execute('''CREATE        INDEX dhash_index ON dedupitems(dHash);''')

			self.conn.commit()
			# print("Indexes Instantiated")
		# else:
		# 	print("Table exists")

	def commit(self):
		self.log.info("Committing changes to DB.")
		self.conn.commit()

	def itemInDB(self, basePath, internalPath, itemHash):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s AND internalPath=%s AND itemHash=%s;", (basePath, internalPath, itemHash))
		return cur.fetchone()

	def basePathInDB(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		return cur.fetchone()


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
		return cur.fetchone()



	def getByHash(self, itemHash):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE itemHash=%s;", (itemHash, ))
		return cur.fetchall()

	def getOtherHashes(self, itemHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE itemHash=%s AND NOT fsPath=%s;", (itemHash, fsMaskPath))
		return cur.fetchall()

	def getOtherDPHashes(self, dHash, pHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE dHash=%s AND pHash=%s AND NOT fsPath=%s;", (dHash, pHash, fsMaskPath))
		return cur.fetchall()

	def getOtherDHashes(self, dHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE dHash=%s AND NOT fsPath=%s;", (dHash, fsMaskPath))
		return cur.fetchall()

	def getOtherPHashes(self, pHash, fsMaskPath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE pHash=%s AND NOT fsPath=%s;", (pHash, fsMaskPath))
		return cur.fetchall()


	def insertItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None):

		cur = self.conn.cursor()
		cur.execute("INSERT INTO dedupitems (fsPath, internalPath, itemhash, pHash, dHash) VALUES (%s, %s, %s, %s, %s);", (basePath, internalPath, itemHash, pHash, dHash))


	def updateItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None):

		cur = self.conn.cursor()
		cur.execute("UPDATE dedupitems SET itemhash=%s, pHash=%s, dHash=%s WHERE fsPath=%s AND internalPath=%s;", (itemHash, pHash, dHash, basePath, internalPath))

	def deleteLikeBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("DELETE FROM dedupitems WHERE fsPath LIKE %s;", (basePath+"%", ))
		self.conn.commit()

	def deleteBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("DELETE FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		self.conn.commit()

	def getItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		return cur.fetchall()

	def getItemNumberOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM dedupitems WHERE fsPath=%s;", (basePath, ))
		return cur.fetchall()

	def getInternalItemsOnBasePath(self, basePath):
		cur = self.conn.cursor()
		cur.execute("SELECT fsPath,internalPath,itemhash FROM dedupitems WHERE fsPath=%s AND internalPath IS NOT NULL;", (basePath, ))
		return cur.fetchall()

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
		return cur.fetchone()

	def getHashes(self, fsPath, internalPath):

		cur = self.conn.cursor()
		cur.execute("SELECT itemHash,pHash,dHash FROM dedupitems WHERE fsPath=%s AND internalPath=%s;", (fsPath, internalPath))
		ret = cur.fetchone()
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
		print("Ret = ", ret[0])
		ret = [(item[0], item[1]) for item in ret]
		return set(ret)

if __name__ == "__main__":

	logSetup.initLogging()
	ind = DbInterface()


