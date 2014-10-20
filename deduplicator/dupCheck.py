


import UniversalArchiveReader
import os
import os.path
import logging

import hashFile
import dbApi

import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb
print("Using cythoned hamming database system")

# Checks an archive (`archPath`) against the contents of the database
# accessible via the `settings.dedupApiFile` python file, which
# uses the absolute-import tool in the current directory.

# isBinaryUnique() returns True if the archive contains any unique items,
# false if it does not.

# isPhashUnique() returns True if the archive contains any phashes, False otherwise.
# The threhold for uniqueness is specified in PHASH_DISTANCE_THRESHOLD,
# which specifies the allowable hamming edit-distance between phash
# values that are still classified as identical. 1-3 are reasonable.
# 0 causes the call to behave very similarly to isBinaryUnique(),
# possibly allowing for extremely minor resave changes.

# deleteArch() deletes the archive which has path archPath,
# and also does the necessary database manipulation to reflect the fact that
# the archive has been deleted.


PHASH_DISTANCE_THRESHOLD = 2

class ArchChecker(object):
	def __init__(self, archPath):
		self.archPath = archPath
		self.arch     = UniversalArchiveReader.ArchiveReader(archPath)
		self.db       = dbApi.DbApi()
		self.log      = logging.getLogger("Main.Deduper")

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
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False

	def simplePhashCheck(self):
		self.log.info("Checking if %s contains any unique files.", self.archPath)

		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dHash, imX, imY = hashFile.hashFile(self.archPath, fileN, fileCtnt.read())
			# print("Hashes", pHash, dHash, hexHash)
			dupsIn = self.db.getOtherDPHashes(dHash, pHash, fsMaskPath="LOLWATTTTTTTTT")
			dups = []
			for fsPath, internalPath, itemhash in dupsIn:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, itemhash))
				else:
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.db.deleteBasePath(fsPath)


			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("It contains at least one unique files.")
				return True

		self.log.info("It does not contain any unique files.")
		return False

	# Do phash checking against self.archPath, but load all local (e.g. in the same dir) phashes into a BK tree,
	# and use that for proper distance searching.
	# This is a stop-gap measure prior to proper PostgreSQL hamming distance searching.
	# Basically, it's a keyhole optimization that exploits the fact that I can be
	# *generally* confident that any duplicates will be in the same directory, which
	# MASSIVELY reduces the problem space, and means that the set of hashes to search is no longer
	# prohibitive to query for on a per-scanned-archive basis
	def localBKPhash(self, dirPath):

		self.db.deleteBasePath(self.archPath)

		self.log.info("Scanning for phash duplicates within directory '%s'", dirPath)
		items = self.db.getLikeBasePath(dirPath)
		self.log.info("Found %s items in dir. Building tree", len(items))

		tree = hamDb.BkHammingTree()
		for row in [row for row in items if row[3]]:
			pHash = int(row[3], 2)
			tree.insert(pHash, row)

		self.log.info("Done. Searching")


		for fileN, fileCtnt in self.arch:
			dummy_fName, dummy_hexHash, pHash, dummy_dHash, dummy_imX, dummy_imY = hashFile.hashFile(self.archPath, fileN, fileCtnt.read())
			pHash = int(pHash, 2)
			matches = tree.getWithinDistance(pHash, PHASH_DISTANCE_THRESHOLD)


			dups = []
			for fsPath, internalPath, itemhash, pHash, dHash, imX, imY in matches:
				if os.path.exists(fsPath):
					dups.append((fsPath, internalPath, itemhash))
				else:
					self.log.info("Item '%s' no longer exists - Removing from database!", fsPath)
					self.db.deleteBasePath(fsPath)

			# Short circuit on unique item, since we are only checking if ANY item is unique
			if not dups:
				self.log.info("Archive contains at least one unique file(s).")
				return True


		self.log.info("Archive does not contain any unique file(s).")
		return False


	def isPhashUnique(self):
		dirPath = os.path.split(self.archPath)[0]

		if os.path.isdir(dirPath) and len(os.listdir(dirPath)) < 500:
			return self.localBKPhash(dirPath)
		else:
			return self.simplePhashCheck()



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

		self.log.info("Hashing file %s" % self.archPath)

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
				fName, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(self.archPath, fName, fCont, shouldPhash=shouldPhash)

				baseHash, oldPHash, oldDHash = self.db.getHashes(self.archPath, fName)
				if all((baseHash, oldPHash, oldDHash)):
					self.log.warn("Item is not duplicate?")
					self.log.warn("%s, %s, %s, %s, %s", self.archPath, fName, hexHash, pHash, dHash)

				if baseHash:
					self.db.updateItem(basePath=self.archPath, internalPath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
				else:
					self.db.insertIntoDb(fspath=self.archPath, internalpath=fName, itemHash=hexHash, pHash=pHash, dHash=dHash)
			except IOError as e:
				self.log.error("Invalid/damaged image file in archive!")
				self.log.error("Archive '%s', file '%s'", self.archPath, fName)
				self.log.error("Error '%s'", e)


		archIterator.close()

		self.log.info("File hashing complete.")

def go():

	import logSetup
	logSetup.initLogging()

	checker = ArchChecker("/media/Storage/MP/Nanatsu no Taizai [++++]/Nanatsu no Taizai - Chapter 96 - Chapter 96[MangaJoy].zip")
	checker.isPhashUnique()
	# checker.addNewArch()


if __name__ == "__main__":
	go()

