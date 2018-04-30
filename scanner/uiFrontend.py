
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
		pbar = tqdm

		skipped = 0
		match = 0
		clean = 0
		processed = 0

		pbar = tqdm.tqdm()
		while scanner.runState.run:

			try:
				item = self.hashQueue.get(timeout=0.1)
				pbar.update()

				if item == "skipped":
					skipped +=1
				elif item == "hash_match":
					match += 1
				elif item == "clean":
					clean += 1
				elif item == "processed":
					processed += 1

				else:
					print()
					print()
					print("WAT?")
					print()
					print(item)
					print()
					print()

				pbar.set_description("%s remaining, %s skipped, %s match, %s clean, %s processed" % (
					self.processingHashQueue.qsize(), skipped, match, clean, processed
					))


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
