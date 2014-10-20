#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import sys
import logSetup

import multiprocessing
import runState

import logging

import random
random.seed()

import signal
import uiFrontend
import fileHasher
import time
import types


class DedupScanTool(object):
	def __init__(self, scanConf):


		logSetup.initLogging()
		self.log = logging.getLogger("Main.Scanner")

		try:
			self.threads = int(scanConf.threadNo)
		except:
			self.threads = 2

		try:
			self.doPhash = not bool(scanConf.noPhash)
		except:
			self.doPhash = True

		try:
			self.checkIntegrity = not bool(scanConf.noIntegrityCheck)
		except:
			self.checkIntegrity = True



		self.toProcessQueue = multiprocessing.Queue()
		self.processedHashQueue = multiprocessing.Queue()
		self.readout = uiFrontend.UiReadout(self.processedHashQueue, self.toProcessQueue)
		self.readout.startThread()




		self.log.info("Initializing %s scanning threads.", self.threads)
		self.hashEngine = fileHasher.HashEngine(self.toProcessQueue, self.processedHashQueue, self.threads, self.doPhash, integrity=self.checkIntegrity)
		self.hashEngine.runThreads()
		self.log.info("File scanning threads running.")


		# endHashes, endZips = len(self.pikDict["hashDict"]), len(self.pikDict["pathDict"])
		# print "Completed dictionary items: Hashes %d, zip files %d" % (endHashes, endZips)
		# print "Deltas: Hashes %d, zip files %d" % (endHashes-startHashes, endZips-startZips)
		# print "Dictionary cleaned"
		# print


	def queueFolderContents(self, cmdArgs):


		targetDir = cmdArgs.sourcePath



		self.log.info("Target Directory = %s", targetDir)

		if not os.path.exists(targetDir):
			self.log.error("Invalid path")
			self.log.error("Please enter a valid path")
			sys.exit()

		scanPath = os.path.abspath(targetDir)
		self.log.info("Scanpath = %s", scanPath)


		scanPath = os.path.abspath(targetDir)

		if cmdArgs.purge:
			self.log.warning("Purging all extant scan results on specified path")
			if os.path.isdir(targetDir):
				self.hashEngine.dbApi.deleteLikeBasePath(targetDir+"/")
			else:
				self.hashEngine.dbApi.deleteBasePath(targetDir)
			self.log.warning("Purge complete.")
		elif not cmdArgs.noCleanTemps:
			self.log.info("Checking for removed files.")
			self.hashEngine.cleanPathCache(targetDir)
			self.log.info("Check complete")
		else:
			self.log.info("Skipping removed file check!.")

		if self.checkIntegrity:
			self.log.info("Verifying archive checksums.")
		else:
			self.log.info("Not verifying archive checksums.")


		if not runState.run:
			return

		self.log.info("Starting scan.")

		try:
			for root, dummy_dirs, files in os.walk(scanPath):
				#print root, dir#, files
				for fileN in files:
					wholePath = os.path.join(root, fileN)
					# print("File", wholePath)
					self.toProcessQueue.put((wholePath, fileN))

		except (KeyboardInterrupt, SystemExit, GeneratorExit):

			self.log.info("Exiting early due to keyboard interrupt:")
			# self.log.info("Scanned %d files.", len(self.pikDict["hashDict"]))
			raise

		except:
			self.log.critical("UNHANDLED ERROR. Emergency state save!")
			# self.dumpVals()
			raise


		#for key, value in pathDict.iteritems():
		#	print key, value

		sys.stdout.write("\r")
		self.log.info("Directory enumeration complete.")

	def waitComplete(self):

		self.log.info("Waiting for all queued file scans complete.")

		self.toProcessQueue.close()
		self.toProcessQueue.join_thread()

		self.log.info("Pending files flushed. Telling worker pool to halt when finished.")

		self.hashEngine.gracefulShutdown()
		self.readout.gracefulShutdown()
		self.log.info("Complete. Exiting.")

	def sigIntHandler(self, dummy_signal, dummy_frame):
		if runState.run:
			print("")
			print("SIGINT Received: Telling threads to stop")
			runState.run = False
			self.hashEngine.haltEarly()

		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt

def doScan(scanConf):


	ddT = DedupScanTool(scanConf)

	signal.signal(signal.SIGINT, ddT.sigIntHandler)
	print("Doing scan")
	print("Progress spinner legend:")
	print("'-', '|' - File processed normally")
	print("'/', '\\' - File MD5 matches existing scan, not processed further")
	print("'*', 'x' - File skipped")
	print("'D', 'd' - File existence checked (only during deleted item purge step)")

	ddT.queueFolderContents(scanConf)
	ddT.waitComplete()

	print("Scan Complete")
	runState.run = False
