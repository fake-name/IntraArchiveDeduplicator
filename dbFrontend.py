
import dbApi
import runState
import logging
import os.path
import queue
import threading
import time


import sys

class Spinner(object):
	def __init__(self):
		# outStr = "-\\|/"
		self.outStr  = "|-"
		self.outStar = "*x"
		self.outMatch = r"\/"
		self.outClean = "Dd"
		self.outInt = 0
		self.x = 0

		self.itemLen = len(self.outStr)

	def next(self, star=False, clean=False, hashmatch=False):
		self.outInt = (self.outInt + 1) % 80

		#sys.stdout.write( "\r%s\r" % outStrs[self.outInt])
		if self.outInt == 0:
			sys.stdout.write("\r")
			self.x = (self.x + 1) % self.itemLen

		if star:
			sys.stdout.write(self.outStar[self.x])
		elif clean:
			sys.stdout.write(self.outClean[self.x])
		elif hashmatch:
			sys.stdout.write(self.outMatch[self.x])
		else:
			sys.stdout.write(self.outStr[self.x])


		sys.stdout.flush()


class DatabaseUpdater(object):
	def __init__(self, hashQueue, monitorQueue):
		self.log = logging.getLogger("Main.DbInt")
		self.dbInt = dbApi.DbApi()
		self.hashQueue = hashQueue

		self.processingHashQueue = monitorQueue

		self.stopOnEmpty = False
		self.stopped = False

		self.spinner = Spinner()

	def cleanPathCache(self, fqPathBase):

		self.log.info("Querying for all files on specified path.")

		itemsCursor = self.dbInt.getUniqueOnBasePath(fqPathBase)
		items = []
		retItems = 0
		for item in itemsCursor:
			retItems += 1
			items.append(item[0])
			if not runState.run:
				print("Breaking due to exit flag")
				return

		self.log.info("Looking for files in the DB that are not on disk anymore.")

		self.log.info("Recieved items = %d", retItems)
		self.log.info("total unique items = %s", len(items))


		for itemPath in items:
			if not os.path.exists(itemPath):
				self.log.info("Item %s does not exist. Should delete from DB", itemPath)
				self.dbInt.deleteBasePath(itemPath)

			if not runState.run:
				print("Breaking due to exit flag")
				return

			self.spinner.next(clean=True)

	def run(self):
		commits = 0
		while runState.run:

			try:
				item = self.hashQueue.get(timeout=0.1)
				if item == "skipped":
					self.spinner.next(star=True)
					continue
				if item == "hash_match":
					self.spinner.next(hashmatch=True)
					continue

				basePath, internalPath, itemHash, pHash, dHash = item
				if basePath.startswith("/content"):
					basePath = basePath.replace("/content", "/media/Storage/Scripts")
				baseHash, oldPHash, oldDHash = self.dbInt.getHashes(basePath, internalPath)
				if all((baseHash, oldPHash, oldDHash)):
					self.log.critical("Already hashed item?")
					self.log.critical("%s, %s, %s, %s, %s", basePath, internalPath, itemHash, pHash, dHash)

				if baseHash:
					# print("Updating DB", basePath, internalPath, itemHash, pHash, dHash)
					self.dbInt.updateItem(basePath, internalPath, itemHash, pHash, dHash)
				else:
					self.dbInt.insertItem(basePath, internalPath, itemHash, pHash, dHash)
				# self.log.info("Item = %s, %s, %s, %s, %s", basePath, internalPath, itemHash, pHash, dHash)
				# self.log.info("Queue Items = %s", self.hashQueue.qsize())
				self.spinner.next()

				commits += 1
				if commits % 250 == 0:
					self.log.info("Have ~%s items remaining to process" % self.processingHashQueue.qsize())
					self.dbInt.commit()
			except queue.Empty:
				if self.stopOnEmpty:
					break
				pass

		self.dbInt.commit()
		self.log.info("DbInterface Exiting, %s")
		self.stopped = True

	def startThread(self):
		self.log.info("Starting thread")
		dbTh = threading.Thread(target=self.run)
		dbTh.start()
		self.log.info("Thread started")


	def gracefulShutdown(self):
		self.stopOnEmpty = True
		while not self.stopped:
			time.sleep(0.5)
