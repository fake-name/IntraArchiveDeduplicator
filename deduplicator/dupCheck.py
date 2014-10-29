


import UniversalArchiveReader
import os
import os.path
import logging
import server.tree
import hashFile
import dbApi
import shutil
import traceback
import threading
import sql.operators as sqlo

import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb

PHASH_DISTANCE_THRESHOLD = 2


class TreeRoot(hamDb.BkHammingTree):

	# Make it a borg class (all instances share state)
	_shared_state = {}
	rootPaths = []
	nodeQuantity = 0
	def __init__(self):

		self.__dict__ = self._shared_state

		# Updating the tree is re-entrant (insert and loadTree)
		# Therefore, we need a RLock
		self.updateLock = threading.RLock()

		self.db       = dbApi.DbApi()
		self.log      = logging.getLogger("Main.Tree")


		super().__init__()

	def loadTree(self, treeRootPath):

		if any([path in treeRootPath for path in self.rootPaths]):
			# print(self.rootPaths, treeRootPath)
			self.log.info("Path already loaded: '%s'", treeRootPath)
			return

		self.log.info("Querying contents of '%s' for loading.", treeRootPath)
		items = self.db.getLike('fsPath', treeRootPath, wantCols=['dbId', 'pHash'])
		self.log.info("Found %s items in dir. Building tree", len(items))


		with self.updateLock:
			for dbId, pHash in items:
				if not pHash:
					continue
				if not isinstance(dbId, int):
					raise ValueError("Node data must be an integer row ID")
				self.insert(pHash, dbId)
			self.rootPaths.append(treeRootPath)

		self.log.info("Directory loaded!")

	def remove(self, *args, **kwargs):
		with self.updateLock:
			self.nodeQuantity -= 1
			super().remove(*args, **kwargs)

	def insert(self, *args, **kwargs):
		with self.updateLock:
			self.nodeQuantity += 1
			super().insert(*args, **kwargs)


	def treeLoaded(self):
		return bool(self.root)

	# We have to be careful, because if we try to remove a item outside the tree's
	# envelope, we'll get a KeyError. Therefore, we intercept calls to remove, require an
	# additional parameter (the path of the file containing the item we're removing),
	# and verify that the item that is being removed is valid to remove.
	# I'm doing this rather then just blindly catching KeyError because I want
	# any attempts to remove a key that /should/ be in the dict to still error.
	def remove(self, filePath, nodeHash, nodeData):
		if any([filePath.startswith(rootPath) for rootPath in self.rootPaths]):
			super().remove(nodeHash, nodeData)


class DbBase(object):
	def __init__(self):

		self.db = dbApi.DbApi()


	def convertDbIdToPath(self, inId):
		return self.db.getItems(wantCols=['fsPath', "internalPath"], dbId=inId).pop()


class TreeProcessor(DbBase):

	def __init__(self, matchDir, removeDir, distanceThresh, callBack=None):
		super().__init__()
		self.log      = logging.getLogger("Main.Processor")

		print("Loading treestructure for path '%s'" % matchDir)
		self.root = TreeRoot()
		self.matchDir = matchDir

		# This doesn't seem to fit too well as a class attribute here, but I cannot
		# Think of anywhere else to put it.
		self.distance = distanceThresh

		# Items are moved to removeDir for manual deletion
		self.delProxyDir = removeDir
		self.root.loadTree(matchDir)

		self.callBack = callBack


	def getMatches(self, item):

		# If the item doesn't have a phash (not an image?), check for binary duplicates
		if not item['pHash']:

			where = (sqlo.Like(self.root.db.table.fspath, self.matchDir+'%') & (self.root.db.table.itemhash == item['itemHash']))
			matches = self.root.db.getItems(wantCols=["dbId"], where=where)

			return matches

		# For items where we have a phash, look it up.
		matches = self.root.getWithinDistance(item['pHash'], self.distance)
		if item['dbId'] in matches:
			matches.remove(item['dbId'])

		ret = []
		for match in matches:
			itemPath, dummy_intpath = self.convertDbIdToPath(match)
			if itemPath != item["fsPath"]:
				if os.path.exists(itemPath):
					ret.append(match)
				else:
					self.log.warn("Item '%s' no longer exists. Removing from tree.", itemPath)
					self.log.warn("Existance check: %s", os.path.exists(itemPath))
					try:
						self.removeArchive(itemPath)
					except KeyError:
						self.log.warn("Item already removed?")



		# print("phash matches", matches)
		return matches


	def trimTree(self, fileItems):
		for item in fileItems:
			self.root.remove(item['fsPath'], item['pHash'], item['dbId'])


	def scanItems(self, internalItems):

		pathMatches = {}
		seen = [0] * len(internalItems)
		offset = 0
		for item in internalItems:
			fMatches = self.getMatches(item)
			if not fMatches:
				self.log.info("Not duplicate: '%s'", item['fsPath'])
				return False
			for match in fMatches:
				seen[offset] += 1

				itemPath, intPath = self.convertDbIdToPath(match)

				# skip items that are missing
				if os.path.exists(itemPath):
					if itemPath not in pathMatches:
						pathMatches[itemPath] = set()
					pathMatches[itemPath].add(intPath)

			offset += 1
		if not all(seen):
			self.log.error("Wat? Not all items seen and yet loop is complete?")
			raise ValueError("Wat? Not all items seen and yet loop is complete?")

		return pathMatches

	# So this is rather confusing. We want to determine the "best" match, but we have
	# a lot of spurious matches.
	# As such, we count the number of distinct matches, then the total number of items in
	# the matching file, and sort using those parameters, and chose the one with the most distinct
	# matches, using the file quantities as the tie-breaker.
	# I have some ideas for using multiple
	def processMatches(self, filePath, pathMatches):

		items = []
		for archPath, intItemSet in pathMatches.items():

			itemNum = self.root.db.getNumberOfPhashes(fsPath=archPath)

			items.append((len(intItemSet), itemNum, archPath))
			# print("archPath, intItemSet", archPath, len(intItemSet), itemNum)

		# Do the actual sort
		items.sort(reverse=True)
		baseItemNum = self.root.db.getNumberOfPhashes(fsPath=filePath)
		for commonSet, matchSize, matchFilePath in items[:5]:
			self.log.info("	Match: '%s', '%s', %s', '%s'", baseItemNum, commonSet, matchSize, matchFilePath)


		items.sort(reverse=True)
		return items[0][-1]


	# Called once for each distinct file on scanned path.
	# Fileitems are the contained files within the scanned file, if any
	def processFile(self, filePath, fileItems):
		self.log.info("Processing file '%s'", filePath)

		if not os.path.exists(filePath):
			self.log.error("Item no longer exists = '%s'", filePath)
			return

		# Only look at files where there are phashes contained
		if not any([item['pHash'] != None for item in fileItems]):
			return

		# There should only be one item with no internal path (the containing archive)
		# Check this to be sure
		if len([item for item in fileItems if not item['internalPath']]) != 1:
			self.log.error("Multiple no-path items?")
			return

		internalItems = [item for item in fileItems if item['internalPath']]

		pathMatches = self.scanItems(internalItems)
		if not pathMatches:
			return

		self.log.info("Item is NOT unique '%s'", filePath)
		bestMatch = self.processMatches(filePath, pathMatches)

		if self.callBack:
			self.callBack(filePath, bestMatch)
		self.handleDuplicate(filePath, bestMatch)

	def handleDuplicate(self, deletedFile, bestMatch):

		# When we have a callback, call the callback so it can do whatever it need to
		# with the information about the duplicate.


		dst = deletedFile.replace("/", ";")
		dst = os.path.join(self.delProxyDir, dst)
		self.log.info("Moving item from '%s'", deletedFile)
		self.log.info("	to '%s'", dst)
		try:
			shutil.move(deletedFile, dst)
		except KeyboardInterrupt:
			raise
		except OSError:
			self.log.error("ERROR - Could not move file!")
			self.log.error(traceback.format_exc())





	def trimFiles(self, targetDir):
		self.log.info("Trimming files on path '%s'", targetDir)
		delItems = self.root.db.getFileDictLikeBasePath(targetDir)
		self.log.info("Have %s items", len(delItems))



		# We want to scan items from the item with the least contained items to the item with the most contained items
		# Therefore, we convert the key array to a list of ({itemLen}, {itemKey}) 2-tuples, sort on that, and then use
		# that list for iterating
		items = list([(len(delItems[key]), key) for key in delItems.keys()])
		items.sort()


		processed = 0
		for dummy_len, filePath in items:
			self.processFile(filePath, delItems[filePath])

			processed += 1
			if processed % 100 == 0:
				print("Loop ", processed)

	def removeArchive(self, itemPath):
		items = self.root.db.getItemsOnBasePath(itemPath)
		for fsPath, dummy_internalPath, dummy_itemhash, pHash, dbId in items:
			if pHash:
				pHash = int(pHash, 2)
				self.root.remove(fsPath, pHash, dbId)

	@classmethod
	def phashScan(cls, args):

		import logSetup
		logSetup.initLogging()

		print("Scan settings:")
		print("targetDir    =", args.targetDir)
		print("removeDir    =", args.removeDir)
		print("scanEnv      =", args.scanEnv)
		print("compDistance =", args.compDistance)

		callback = None
		if 'callback' in args:
			callback = args['callback']



		tree = cls(args.scanEnv, args.removeDir, args.compDistance, callBack=callback)
		tree.trimFiles(args.targetDir)



class ArchChecker(DbBase):

	def __init__(self, archPath):
		super().__init__()
		self.archPath    = archPath
		self.arch        = UniversalArchiveReader.ArchiveReader(archPath)


		self.log = logging.getLogger("Main.Deduper")
		self.log.info("ArchChecker Instantiated")

	def isBinaryUnique(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		for dummy_fileN, fileCtnt in self.arch:
			hexHash = hashFile.getMd5Hash(fileCtnt.read())

			dupsIn = self.db.getOtherHashes(hexHash, fsMaskPath=self.archPath)
			dups = []
			for fsPath, internalPath, dummy_itemhash in dupsIn:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, dummy_itemhash))
				else:
					self.log.warn("Item '%s' no longer exists!", fsPath)
					# self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False


	def isPhashUnique(self, searchDistance=PHASH_DISTANCE_THRESHOLD):

		self.db.deleteBasePath(self.archPath)

		self.log.info("Scanning for phash duplicates.")

		# TreeRoot will share state with all other instances of treeRoot, so
		# the tree structure will therefore persist.
		if not server.tree.tree:
			self.log.info("Tree not instantiated. Creating")
			server.tree.tree = TreeRoot()

		tree = server.tree.tree


		self.log.info("Done. Searching")


		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dummy_dHash, dummy_imX, dummy_imY = hashFile.hashFile(self.archPath, fileN, fileCtnt.read())
			pHash = int(pHash, 2)

			matches = tree.getWithinDistance(pHash, searchDistance)
			# print(matches)

			dups = []
			for dbId in matches:
				try:
					fsPath, internalPath = self.convertDbIdToPath(dbId)

					if os.path.exists(fsPath):
						dups.append((fsPath, internalPath))
					else:
						self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
						self.log.warn("Existance check: %s", os.path.exists(fsPath))
						# self.db.deleteBasePath(fsPath)

				except IndexError:
					print("Error when getting fsPath!")
					print("DbId = ", dbId)
					print("Working arch = ", self.archPath)


			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("Archive contains at least one unique phash(es).")
				return True


		self.log.info("Archive does not contain any unique phashes.")
		return False




	def getHashes(self, shouldPhash=True):


		self.log.info("Getting item hashes for %s.", self.archPath)
		ret = []
		for fileN, fileCtnt in self.arch:
			ret.append(hashFile.hashFile(self.archPath, fileN, fileCtnt.read(), shouldPhash=shouldPhash))


		self.log.info("%s Fully hashed.", self.archPath)
		return ret

	def deleteArch(self):

		self.log.warning("Deleting archive '%s'", self.archPath)
		self.db.deleteBasePath(self.archPath)
		os.remove(self.archPath)


	def addNewArch(self, shouldPhash=True):

		self.log.info("Hashing file %s", self.archPath)

		self.db.deleteBasePath(self.archPath)

		# Do overall hash of archive:
		with open(self.archPath, "rb") as fp:
			hexHash = hashFile.getMd5Hash(fp.read())
		self.db.insertIntoDb(fspath=self.archPath, internalpath="", itemhash=hexHash)


		# Next, hash the file contents.
		archIterator = UniversalArchiveReader.ArchiveReader(self.archPath)
		for fName, fp in archIterator:

			fCont = fp.read()
			try:
				fName, hexHash, pHash, dHash, dummy_imX, dummy_imY = hashFile.hashFile(self.archPath, fName, fCont, shouldPhash=shouldPhash)

				baseHash, oldPHash, oldDHash = self.db.getHashes(self.archPath, fName)
				if all((baseHash, oldPHash, oldDHash)):
					self.log.warn("Item is not duplicate?")
					self.log.warn("%s, %s, %s, %s, %s", self.archPath, fName, hexHash, pHash, dHash)

				if baseHash:
					self.db.updateItem(fspath=self.archPath, internalpath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
				else:
					self.db.insertIntoDb(fspath=self.archPath, internalpath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)

				ids = self.db.getItems(wantCols=["dbId"], fspath=self.archPath, internalpath=fName)
				if len(ids) != 1:
					self.log.error("More then one item inserted? Wat?")

				hashId = ids[0][0]
				server.tree.tree.insert(pHash, hashId)




			except IOError as e:
				self.log.error("Invalid/damaged image file in archive!")
				self.log.error("Archive '%s', file '%s'", self.archPath, fName)
				self.log.error("Error '%s'", e)


		archIterator.close()

		self.log.info("File hashing complete.")


def phashScan(args):
	TreeProcessor.phashScan(args)


def go():

	import logSetup
	logSetup.initLogging()

	checker = ArchChecker("/media/Storage/MP/Nanatsu no Taizai [++++]/Nanatsu no Taizai - Chapter 96 - Chapter 96[MangaJoy].zip")
	checker.isPhashUnique()
	# checker.addNewArch()


if __name__ == "__main__":
	go()

