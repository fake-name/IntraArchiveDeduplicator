#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import time
import sys
import logSetup

import multiprocessing
import runState

import logging

import random
random.seed()

import dbApi

import signal
import dbFrontend
import fileHasher

import types




class DedupScanTool(object):
	def __init__(self, scanConf):


		logSetup.initLogging()
		self.log = logging.getLogger("Main.Scanner")

		try:
			self.threads = int(scanConf.threadNo)
		except:
			self.threads = 2

		print("Opening DB")
		self.toProcessQueue = multiprocessing.Queue()
		self.processedHashQueue = multiprocessing.Queue()
		self.dbTool = dbFrontend.DatabaseUpdater(self.processedHashQueue, self.toProcessQueue)
		self.dbTool.startThread()
		print("Opened.")


		self.log.info("Initializing scanning threads.")
		self.hashEngine = fileHasher.HashEngine(self.toProcessQueue, self.processedHashQueue, self.threads)
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
			self.dbTool.dbInt.deleteBasePath(targetDir)
			self.log.warning("Purge complete.")
		elif not cmdArgs.noCleanTemps:
			self.log.info("Checking for removed files.")
			self.dbTool.cleanPathCache(targetDir)
			self.log.info("Check complete")


		if not runState.run:
			return

		self.log.info("Starting scan.")

		try:
			for root, dummy_dirs, files in os.walk(scanPath):
				#print root, dir#, files
				for fileN in files:
					wholePath = os.path.join(root, fileN)
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
		self.hashEngine.gracefulShutdown()
		self.dbTool.gracefulShutdown()
		self.log.info("Complete. Exiting.")

	def sigIntHandler(self, dummy_signal, dummy_frame):
		if runState.run:
			print("")
			print("SIGINT Received: Telling threads to stop")
			runState.run = False
			self.hashEngine.gracefulShutdown()

		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt

def doScan(scanConf):


	ddT = DedupScanTool(scanConf)

	signal.signal(signal.SIGINT, ddT.sigIntHandler)
	print("Doing scan")

	ddT.queueFolderContents(scanConf)
	ddT.waitComplete()

	runState.run = False


if __name__ == "__main__":


	# from pycallgraph import PyCallGraph
	# from pycallgraph.output import GraphvizOutput

	# graphviz = GraphvizOutput(output_file='filter_none.png')

	# with PyCallGraph(output=graphviz):

	conf = types.SimpleNamespace()
	conf.purge = False
	conf.noCleanTemps = True
	# conf.sourcePath = '/media/Storage/MP'
	conf.sourcePath = '/content/XaDownloads'

	doScan(conf)


	# parser = argparse.ArgumentParser()
	# subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands')

	# ddTool = DedupTool()

	# parserDirScan = subparsers.add_parser('dir-scan', help="Scan set of directory, and generate a list of hashes of all the files therein")
	# parserDirScan.add_argument('-i', '--in-folder', required=True, dest="sourcePath")
	# parserDirScan.add_argument('-c', '--clean', required=False, dest="cleanTemps", action='store_true')

	# parserDirScan.set_defaults(func=ddTool.queueFolderContents)


	# # parserDirScan = subparsers.add_parser('dir-clean', help="Load set of cached hashes, and move all duplicate zips therein")
	# # parserDirScan.add_argument('-i', '--in-file', required=True, dest="cacheFilesPath")

	# # parserDirScan.add_argument('--move', required=False, dest="movePath")
	# # parserDirScan.add_argument('--move-go', required=False, dest="doMove", action='store_true')


	# # parserDirScan.set_defaults(func=ddTool.deepCleanDirs)

	# try:
	# 	args = parser.parse_args()
	# 	args.func(args)
	# except KeyboardInterrupt:
	# 	print("Swallowed KeyboardInterrupt")
	# 	print("Exiting")
	# 	sys.exit()

