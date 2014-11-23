#!/usr/bin/python
# -*- coding: utf-8 -*-


import queue
import scanner.runState

import UniversalArchiveInterface

import multiprocessing

import magic
import logging
import dbApi
import signal

import os.path

import random
random.seed()

import scanner.hashFile as hasher

import traceback

IMAGE_EXTS = ("bmp", "eps", "gif", "im", "jpeg", "jpg", "msp", "pcx", "png", "ppm", "spider", "tiff", "webp", "xbm")
ARCH_EXTS = ("zip", "rar", "cbz", "cbr", "7z", "cb7")

class HashEngine(object):


	def __init__(self, inputQueue, outputQueue, threads=2, pHash=True, integrity=True):
		self.log           = logging.getLogger("Main.HashEngine")
		self.tlog          = logging.getLogger("Main.HashEngineThread")
		self.hashWorkers   = threads
		self.inQ           = inputQueue
		self.outQ          = outputQueue
		self.doPhash       = pHash
		self.archIntegrity = integrity

		self.runStateMgr   = multiprocessing.Manager()
		self.manNamespace  = self.runStateMgr.Namespace()
		self.dbApi         = dbApi.DbApi()



	def runThreads(self):
		self.manNamespace.stopOnEmpty = False
		self.manNamespace.run = True
		args = (self.inQ,
			self.outQ,
			self.manNamespace,
			self.doPhash,
			True,
			self.archIntegrity)

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


	def cleanPathCache(self, fqPathBase):

		self.log.info("Querying for all files on specified path.")

		itemsCursor = self.dbApi.getUniqueOnBasePath(fqPathBase)
		items = []
		retItems = 0
		for item in itemsCursor:
			retItems += 1
			items.append(item[0])
			if not scanner.runState.run:
				print("Breaking due to exit flag")
				return

		self.log.info("Looking for files in the DB that are not on disk anymore.")

		self.log.info("Recieved items = %d", retItems)
		self.log.info("total unique items = %s", len(items))


		for itemPath in items:
			if not os.path.exists(itemPath):
				self.log.info("Item %s does not exist. Should delete from DB", itemPath)
				self.dbApi.deleteBasePath(itemPath)

			if not scanner.runState.run:
				print("Breaking due to exit flag")
				return

			self.outQ.put("clean")






def createHashThread(inQueue, outQueue, runMgr, pHash, checkChecksumScannedArches, integrity):
	# Make all the thread-pool threads ignore SIGINT, so they won't freak out on CTRL+C
	signal.signal(signal.SIGINT, signal.SIG_IGN)

	runner = HashThread(inQueue, outQueue, runMgr, pHash, checkChecksumScannedArches, integrity)
	runner.run()

class HashThread(object):


	loggerPath = "Main.HashEngine"

	def __init__(self, inputQueue, outputQueue, runMgr, pHash, checkChecksumScannedArches=True, integrity=True):



		# If we're running as a multiprocessing thread, inject that into
		# the logger path
		threadName = multiprocessing.current_process().name
		if threadName:
			self.tlog = logging.getLogger("%s.%s" % (self.loggerPath, threadName))
		else:
			self.tlog = logging.getLogger(self.loggerPath)

		self.runMgr = runMgr
		self.inQ = inputQueue
		self.outQ = outputQueue
		self.doPhash = pHash
		self.archIntegrity = integrity

		self.checkArchiveChanged = checkChecksumScannedArches

		self.dbApi = dbApi.DbApi()
		self.loops = 0

		self.logger = None




	def run(self):
		try:
			while self.runMgr.run:
				try:
					filePath, fileName = self.inQ.get(timeout=0.5)
					# self.tlog.info("Scan task! %s", filePath)
					self.processFile(filePath)
				except queue.Empty:
					if self.runMgr.stopOnEmpty:
						self.tlog.info("Hashing thread out of tasks. Exiting.")
						break
				# self.tlog.info("HashThread loopin! stopOnEmpty = %s, run = %s", self.runMgr.stopOnEmpty, self.runMgr.run)
		except FileNotFoundError:
			print("Multiprocessing manager shut down?")
			print(traceback.format_exc())

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




	def scanArchive(self, archPath, archData):
		# print("Scanning archive", archPath)

		archIterator = UniversalArchiveInterface.ArchiveReader(archPath, fileContents=archData)

		fnames = [item[0] for item in archIterator]
		fset = set(fnames)
		if len(fnames) != len(fset):
			print(fnames)
			print(fset)
			raise ValueError("Wat?")

		self.dbApi.begin()

		try:
			for fName, fp in archIterator:

				fCont = fp.read()

				fName, hexHash, pHash, dHash, imX, imY = hasher.hashFile(archPath, fName, fCont)

				insertArgs = {
							"fsPath"       :archPath,
							"internalPath" :fName,
							"itemHash"     :hexHash,
							"pHash"        :pHash,
							"dHash"        :dHash,
							"imgX"         :imX,
							"imgY"         :imY
						}


				self.dbApi.insertIntoDb(**insertArgs)
				self.outQ.put("processed")
				if not scanner.runState.run:
					break
		except:
			print(archPath)
			self.dbApi.rollback()
			raise

		self.dbApi.commit()
		archIterator.close()

	def processImageFile(self, wholePath, dbFilePath):

		dummy_itemHash, pHash, dHash = self.dbApi.getHashes(dbFilePath, "")
		# print("Have hashes - ", dummy_itemHash, pHash, dHash)
		if not all((pHash, dHash)):
			with open(wholePath, "rb") as fp:
				fCont = fp.read()
				try:

					fName, hexHash, pHash, dHash, imX, imY = hasher.hashFile(wholePath, "", fCont)

					insertArgs = {
								"fsPath"       :wholePath,
								"internalPath" :fName,     # fname == '' in this case
								"itemHash"     :hexHash,
								"pHash"        :pHash,
								"dHash"        :dHash,
								"imgX"         :imX,
								"imgY"         :imY
							}

					self.dbApi.insertIntoDb(**insertArgs)

					self.outQ.put("processed")

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

		fName, hexHash, pHash, dHash, imX, imY = hasher.hashFile(wholePath, "", fCont)

		insertArgs = {
					"fsPath"       :wholePath,
					"internalPath" :fName,     # fname == '' in this case
					"itemHash"     :hexHash,
					"pHash"        :pHash,
					"dHash"        :dHash,
					"imgX"         :imX,
					"imgY"         :imY
				}

		self.dbApi.insertIntoDb(**insertArgs)

		self.outQ.put("processed")


	def getFileMd5(self, wholePath):

		with open(wholePath, "rb") as fp:
			fCont = fp.read()
		hexHash = hasher.getMd5Hash(fCont)
		return hexHash, fCont


	def processArchive(self, wholePath):


		fType = "none"
		fCont = None
		archHash = self.dbApi.getItemsOnBasePathInternalPath(wholePath, "")
		if not archHash:
			self.dbApi.deleteBasePath(wholePath)
			curHash, fCont = self.getFileMd5(wholePath)

			insertArgs = {
						"fsPath"       :wholePath,
						"internalPath" :'',
						"itemHash"     :curHash
					}
			self.dbApi.insertIntoDb(**insertArgs)
			self.outQ.put("processed")

		elif len(archHash) != 1:
			print("ArchHash", archHash)
			raise ValueError("Multiple hashes for a single file? Wat?")
		else:
			if not self.archIntegrity:
				# print("Skipped", wholePath)
				self.outQ.put("skipped")
				return
			dummy_fPath, dummy_name, haveHash = archHash.pop()
			curHash, fCont = self.getFileMd5(wholePath)

			if curHash == haveHash:
				# print("Skipped", wholePath)
				self.outQ.put("hash_match")
				return
			else:
				self.tlog.warn("Archive %s has changed! Rehashing!", wholePath)
				self.dbApi.deleteBasePath(wholePath)

		# TODO: Use `fCont` to prevent having to read each file twice.


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

		if 	fType == 'application/zip' or \
			fType == 'application/x-rar' or \
			fType == 'application/x-7z-compressed':

			# self.tlog.info("Scanning into archive - %s - %s", fileN, wholePath)

			try:
				self.scanArchive(wholePath, fCont)

			except KeyboardInterrupt:
				raise
			except:
				self.tlog.error("Archive is damaged, corrupt, or not actually an archive: %s", wholePath)
				self.tlog.error("Error Traceback:")
				self.tlog.error(traceback.format_exc())
				# print("wat?")

			# print("Archive scan complete")
			return

	def processFile(self, wholePath):
		if wholePath.startswith("/content"):
			raise ValueError("Wat?")

		# print("path", wholePath)
		if wholePath.lower().endswith(ARCH_EXTS):
			self.processArchive(wholePath)
		else:

			# Get list of all hashes for items on wholePath
			extantItems = self.dbApi.getItemsOnBasePath(wholePath)
			haveFileHashList = [item[2] != "" for item in extantItems]

			# print("Extant items = ", extantItems, wholePath)

			# Only rescan if we don't have hashes for all the items in the archive (no idea how that would happen),
			# or we have no items for the archive

			if all(haveFileHashList) and len(extantItems):

				self.outQ.put("skipped")
				return

			elif wholePath.lower().endswith(IMAGE_EXTS):  # It looks like an image.
				self.processImageFile(wholePath, wholePath)
				# self.tlog.info("Skipping Image = %s", wholePath)

			elif not any([item[2] and not item[1] for item in extantItems]):
				# print("File", wholePath)
				try:
					self.hashBareFile(wholePath, wholePath)

				except IOError:

					self.tlog.error("Something happened to the file before processing (did it get moved?)! ")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())
				except (IndexError, UnboundLocalError):
					self.tlog.error("Error while processing wholePath")
					self.tlog.error("%s", wholePath)
					self.tlog.error("%s", traceback.format_exc())

			else:
				self.outQ.put("skipped")
				# self.tlog.info("Skipping file = %s", wholePath)
