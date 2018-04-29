
import dbApi
import scanner.runState
import logging
import os.path
import queue
import threading
import time

import sys
import tqdm


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


class UiReadout(object):
	def __init__(self, hashQueue, monitorQueue):
		self.log = logging.getLogger("Main.UI")

		self.hashQueue = hashQueue

		self.processingHashQueue = monitorQueue

		self.stopOnEmpty = False
		self.stopped = False

		self.spinner = Spinner()


	def run(self):
		commits = 0
		while scanner.runState.run:

			try:
				item = self.hashQueue.get(timeout=0.1)
				if item == "skipped":
					self.spinner.next(star=True)
					continue
				elif item == "hash_match":
					self.spinner.next(hashmatch=True)
					continue
				elif item == "clean":
					self.spinner.next(clean=True)
					continue
				elif item == "processed":
					self.spinner.next()
					continue

				else:
					print()
					print()
					print("WAT?")
					print()
					print(item)
					print()
					print()


				if commits % 250 == 0:
					self.log.info("Have ~%s items remaining to process" % self.processingHashQueue.qsize())
					self.dbInt.commit()
			except queue.Empty:
				if self.stopOnEmpty:
					break
				pass

		self.log.info("UI Thread Exiting")
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
