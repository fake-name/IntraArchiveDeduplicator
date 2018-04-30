
import dbApi
import scanner.runState
import logging
import os.path
import queue
import threading
import time

import sys
import tqdm


class UiReadout(object):
	def __init__(self, hashQueue, monitorQueue):
		self.log = logging.getLogger("Main.UI")

		self.hashQueue = hashQueue

		self.processingHashQueue = monitorQueue

		self.stopOnEmpty = False
		self.stopped = False



	def run(self):
		commits = 0
		while scanner.runState.run:

			try:
				item = self.hashQueue.get(timeout=0.1)
				if item == "skipped":
					continue
				elif item == "hash_match":
					continue
				elif item == "clean":
					continue
				elif item == "processed":
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
					self.log.info("Have ~%s items remaining to process", self.processingHashQueue.qsize())
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
