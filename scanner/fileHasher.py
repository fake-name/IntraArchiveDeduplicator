#!/usr/bin/python
# -*- coding: utf-8 -*-


import queue
import scanner.runState

import UniversalArchiveInterface as uar

import multiprocessing

import magic
import logging
import dbPhashApi
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
		self.archIntegrity = integrity

		self.runStateMgr   = multiprocessing.Manager()
		self.manNamespace  = self.runStateMgr.Namespace()
		self.dbApi         = dbPhashApi.PhashDbApi()



	def runThreads(self):
		self.manNamespace.stopOnEmpty = False
		self.manNamespace.run = True
		args = (self.inQ,
			self.outQ,
			self.manNamespace,
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

			try:
				if not scanner.runState.run:
					print("Breaking due to exit flag")
					return
			except BrokenPipeError:
				self.log.error("Runstate thread exited? Halting")
				return


			self.outQ.put("clean")






def createHashThread(inQueue, outQueue, runMgr, integrity):
	# Make all the thread-pool threads ignore SIGINT, so they won't freak out on CTRL+C
	signal.signal(signal.SIGINT, signal.SIG_IGN)

	runner = HashThread(inQueue, outQueue, runMgr, integrity)
	runner.run()

class HashThread(object):


	loggerPath = "Main.HashEngine"

	def __init__(self, inputQueue, outputQueue, runMgr, integrity=True):

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
		self.archIntegrity = integrity

		self.dbApi = dbApi.DbApi()

	def putProgQueue(self, value):
		self.outQ.put(value)

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

		except BrokenPipeError:
			print("Multiprocessing manager shut down?")


		self.tlog.info("Scanner exiting.")

		self.inQ.close()
		self.outQ.close()

		self.inQ.join_thread()
		self.outQ.join_thread()




	def scanArchive(self, archPath, archData):
		# print("Scanning archive", archPath)

		archIterator = uar.ArchiveReader(archPath, fileContents=archData)

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
				self.putProgQueue("processed")
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

		self.putProgQueue("processed")


	def getFileMd5(self, wholePath):

		with open(wholePath, "rb") as fp:
			fCont = fp.read()
		hexHash = hasher.getMd5Hash(fCont)
		return hexHash, fCont


	def processArchive(self, wholePath):
		fType = "none"
		fCont = None
		archRow = self.dbApi.getItemsOnBasePathInternalPath(wholePath, "")

		contHashes = self.dbApi.getItemsOnBasePath(wholePath)

		haveImInfo = [(bool(item['imgx']) and bool(item['imgy'])) for item in contHashes if item['pHash']]


		if not all(haveImInfo):
			self.tlog.info("Missing image size information for archive %s. Rescanning.", wholePath)
			self.dbApi.deleteBasePath(wholePath)

		elif len(archRow) > 1:
			# print("archRow", archRow)
			raise ValueError("Multiple hashes for a single file? Wat?")
		elif archRow and archRow[0]['itemhash']:

			if not self.archIntegrity:
				self.putProgQueue("skipped")
				return
			item = archRow.pop()
			curHash, fCont = self.getFileMd5(wholePath)

			if curHash == item['itemhash']:
				# print("Skipped", wholePath)
				self.putProgQueue("hash_match")
				return
			else:
				self.tlog.warn("Archive %s has changed! Rehashing!", wholePath)
				self.dbApi.deleteBasePath(wholePath)

		else:
			if archRow:
				self.tlog.info("Missing whole archive hash! Rescanning!")
			self.dbApi.deleteBasePath(wholePath)
			curHash, fCont = self.getFileMd5(wholePath)

			insertArgs = {
						"fsPath"       :wholePath,
						"internalPath" :'',
						"itemHash"     :curHash
					}
			self.dbApi.insertIntoDb(**insertArgs)
			self.putProgQueue("processed")


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
			haveFileHashList = [item['itemhash'] != "" for item in extantItems]


			# print("Extant items = ", extantItems, wholePath)

			# Only rescan if we don't have hashes for all the items in the archive (no idea how that would happen),
			# or we have no items for the archive

			if all(haveFileHashList) and len(extantItems):

				self.putProgQueue("skipped")
				return

			elif wholePath.lower().endswith(IMAGE_EXTS):  # It looks like an image.
				self.processImageFile(wholePath, wholePath)
				# self.tlog.info("Skipping Image = %s", wholePath)

			# Rehash the overall archive if we don't have a hash-value for the archive with no internalpath.
			elif not any([item['itemhash'] and not item['internalPath'] for item in extantItems]):
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
				self.putProgQueue("skipped")
				# self.tlog.info("Skipping file = %s", wholePath)
