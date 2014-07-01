
import dbApi
import runState
import logging
import os.path
import queue
import threading



import sys

def cmdLineSpinner():
	# outStr = "-\\|/"
	outStr = "|-"
	outInt = 0
	x = 0
	while True:
		outInt = (outInt + 1) % 80

		#sys.stdout.write( "\r%s\r" % outStrs[outInt])
		if outInt == 0:
			sys.stdout.write("\r")
			x = (x + 1) % len(outStr)
		sys.stdout.write(outStr[x])
		sys.stdout.flush()
		yield


class DatabaseUpdater(object):
	def __init__(self, hashQueue):
		self.log = logging.getLogger("Main.DbInt")
		self.dbInt = dbApi.DbApi()
		self.hashQueue = hashQueue

		self.stopOnEmpty = False

		self.spinner = cmdLineSpinner()

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

			next(self.spinner)

	def run(self):
		commits = 0
		while runState.run:

			try:
				item = self.hashQueue.get(timeout=0.1)
				if item == "skipped":
					next(self.spinner)
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
				next(self.spinner)

				commits += 1
				if commits % 250 == 0:
					self.dbInt.commit()
			except queue.Empty:
				if self.stopOnEmpty:
					break
				pass


		self.log.info("DbInterface Exiting")

	def startThread(self):
		self.log.info("Starting thread")
		dbTh = threading.Thread(target=self.run)
		dbTh.start()
		self.log.info("Thread started")


	def gracefulShutdown(self):
		self.stopOnEmpty = True
