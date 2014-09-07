#!/usr/bin/python
# -*- coding: utf-8 -*-


import queue
import runState

import UniversalArchiveIterator

import multiprocessing

import magic
import dbApi
import signal

import logging

import random
random.seed()

from hashFile import hashFile

import traceback

IMAGE_EXTS = ("bmp", "eps", "gif", "im", "jpeg", "jpg", "msp", "pcx", "png", "ppm", "spider", "tiff", "webp", "xbm")
ARCH_EXTS = ("zip", "rar", "cbz", "cbr")

class HashEngine(object):


	def __init__(self, inputQueue, outputQueue, threads=2, pHash=True):
		self.log           = logging.getLogger("Main.HashEngine")
		self.tlog          = logging.getLogger("Main.HashEngineThread")
		self.hashWorkers   = threads
		self.inQ           = inputQueue
		self.outQ          = outputQueue
		self.doPhash       = pHash

		self.runStateMgr   = multiprocessing.Manager()
		self.manNamespace  = self.runStateMgr.Namespace()
		self.dbApi         = dbApi.DbApi()



	def runThreads(self):
		self.manNamespace.stopOnEmpty = False
		self.manNamespace.run = True
		args = (self.inQ,
			self.outQ,
			self.manNamespace,
			self.doPhash)

		self.pool = multiprocessing.pool.Pool(processes=self.hashWorkers, initializer=createHashThread, initargs=args )

	def close(self):
		self.log.info("Closing threadpool")
		self.manNamespace.run = False
		self.pool.terminate()

	def haltEarly(self):
		self.manNamespace.run = False

	def gracefulShutdown(self):


		self.manNamespace.stopOnEmpty = True

		self.pool.close()
		self.pool.join()






def createHashThread(inQueue, outQueue, runMgr, pHash):
	# Make all the thread-pool threads ignore SIGINT, so they won't freak out on CTRL+C
	signal.signal(signal.SIGINT, signal.SIG_IGN)

	runner = HashThread(inQueue, outQueue, runMgr, pHash)
	runner.run()

class HashThread(object):



	def __init__(self, inputQueue, outputQueue, runMgr, pHash):
		self.log = logging.getLogger("Main.HashEngine")
		self.tlog = logging.getLogger("Main.HashEngineThread")
		self.runMgr = runMgr
		self.inQ = inputQueue
		self.outQ = outputQueue
		self.doPhash = pHash

		self.dbApi = dbApi.DbApi()
		self.loops = 0


	def run(self):
		try:
			while self.runMgr.run:
				try:
					filePath, fileName = self.inQ.get(timeout=0.5)
					# self.tlog.info("Scan task! %s", filePath)
					self.processFile(filePath, fileName)
				except queue.Empty:
					if self.runMgr.stopOnEmpty:
						self.tlog.info("Hashing thread out of tasks. Exiting.")
						break
				# self.tlog.info("HashThread loopin! stopOnEmpty = %s, run = %s", self.runMgr.stopOnEmpty, self.runMgr.run)

		except:
			print("Exception in hash tool?")
			traceback.print_exc()

		if not self.runMgr.run:
			self.tlog.info("Scanner exiting due to halt flag.")
		else:
			self.inQ.close()
			self.outQ.close()

			self.inQ.join_thread()
			self.outQ.join_thread()




	def scanArchive(self, archPath):
		# print("Scanning archive", archPath)
		archIterator = UniversalArchiveIterator.ArchiveIterator(archPath)

		for fName, fp in archIterator:

			fCont = fp.read()

			fName, hexHash, pHash, dHash = hashFile(archPath, fName, fCont)

			self.outQ.put((archPath, fName, hexHash, pHash, dHash))


			if not runState.run:
				break


	def processImageFile(self, wholePath, dbFilePath):

		dummy_itemHash, pHash, dHash = self.dbApi.getHashes(dbFilePath, "")
		# print("Have hashes - ", dummy_itemHash, pHash, dHash)
		if not all((pHash, dHash)):
			with open(wholePath, "rb") as fp:
				fCont = fp.read()
				try:
					if self.doPhash:
						fName, hexHash, pHash, dHash = hashFile(wholePath, "", fCont)
					else:
						fName, hexHash, pHash, dHash = hashFile(wholePath, "", fCont)

					self.outQ.put((dbFilePath, fName, hexHash, pHash, dHash))
				except (IndexError, UnboundLocalError):
					self.tlog.error("Error while processing fileN")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())

				# self.log.info("Scanned bare image %s, %s, %s", fileN, pHash, dHash)

		else:
			self.outQ.put("skipped")

	def hashBareFile(self, wholePath, dbPath, doPhash=True):
		with open(wholePath, "rb") as fp:
			fCont = fp.read()
			fName, hexHash, pHash, dHash = hashFile(wholePath, "", fCont, shouldPhash=doPhash)
			self.outQ.put((dbPath, fName, hexHash, pHash, dHash))

	def processFile(self, wholePath, fileN):

		fType = "none"


		if wholePath.startswith("/content"):
			dbFilePath = wholePath.replace("/content", "/media/Storage/Scripts")
		else:
			dbFilePath = wholePath

		extantItems = self.dbApi.getItemsOnBasePath(dbFilePath)
		# print("Extant items = ", extantItems, wholePath)


		haveFileHashList = [item[2] != "" for item in extantItems]


		# Only rescan if we don't have hashes for all the items in the archive (no idea how that would happen),
		# or we have no items for the archive
		if not (all(haveFileHashList) and len(extantItems)):

			if fileN.endswith(ARCH_EXTS):
				try:
					fType = magic.from_file(wholePath, mime=True)
					fType = fType.decode("ascii")
				except magic.MagicException:
					self.tlog.error("REALLY Corrupt Archive! ")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())
					fType = "none"
				except IOError:
					self.tlog.error("Something happened to the file before processing (did it get moved?)! ")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())
					fType = "none"

				if fType == 'application/zip' or fType == 'application/x-rar':

					# self.tlog.info("Scanning into archive - %s - %s", fileN, wholePath)

					try:
						self.scanArchive(wholePath)

					except KeyboardInterrupt:
						raise
					except:
						self.tlog.error("Archive is damaged, corrupt, or not actually an archive: %s", wholePath)
						self.tlog.error("Error Traceback:")
						self.tlog.error(traceback.format_exc())
						# print("wat?")

					# print("Archive scan complete")
					return

			elif fileN.lower().endswith(IMAGE_EXTS):  # It looks like an image.
				self.processImageFile(wholePath, dbFilePath)
				# self.tlog.info("Skipping Image = %s", fileN)

			elif not any([item[2] and not item[1] for item in extantItems]):
				# print("File", dbFilePath)
				try:
					self.hashBareFile(wholePath, dbFilePath)

				except IOError:

					self.tlog.error("Something happened to the file before processing (did it get moved?)! ")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())
				except (IndexError, UnboundLocalError):
					self.tlog.error("Error while processing fileN")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())

		else:
			self.outQ.put("skipped")
			# self.tlog.info("Skipping file = %s", fileN)
