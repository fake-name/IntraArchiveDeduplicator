


import pArch
import os
import sys
import os.path
import logging
import magic
import shutil
import traceback

import dbPhashApi as dbApi

import multiprocessing
import scanner.fileHasher

PHASH_DISTANCE_THRESHOLD = 2


class ProxyDbBase(object):
	def __init__(self):
		self.db = dbApi.PhashDbApi()

	def convertDbIdToPath(self, inId):
		return self.db.getItems(wantCols=['fsPath', "internalPath"], dbId=inId).pop()


class ArchChecker(ProxyDbBase):
	'''
	Class to encapsulate the required object to check if `archpath` is unique.

	'''


	def __init__(self, archPath, pathFilter=None):
		super().__init__()

		# pathFilter filters
		# Basically, if you pass a list of valid path prefixes, any matches not
		# on any of those path prefixes are not matched.
		# Default is [''], which matches every path, because "anything".startswith('') is true
		self.maskedPaths = pathFilter or ['']

		self.archPath    = archPath
		self.arch        = pArch.PhashArchive(archPath)

		self.log = logging.getLogger("Main.Deduper")
		self.log.info("ArchChecker Instantiated")

	# If getMatchingArchives returns something, it means we're /not/ unique,
	# because getMatchingArchives returns matching files
	def isBinaryUnique(self):
		'''
		Is the archive this class was instantiated on binary unique (e.g. there
		is a byte-for-byte complete duplicate of it) elsewhere on the filesystem,
		that still exists.

		Returns:
			Boolean: True if unique, False if not.
		'''
		ret = self.getMatchingArchives()

		if len(ret):
			return False
		return True

	def isPhashUnique(self, searchDistance=PHASH_DISTANCE_THRESHOLD):
		'''
		Is the archive this class was instantiated on phash unique, where the
		duplicating files elsewhere on the filesystem still exist.

		Phash-unique means there are matches for each of the files in the archive,
		including searching by phash within distance `searchDistance` for any files
		that are images.

		Returns:
			Boolean: True if unique, False if not.
		'''
		ret = self.getPhashMatchingArchives(searchDistance)

		if len(ret):
			return False
		return True


	def getBestBinaryMatch(self):
		'''
		Get the filesystem path of the "best" matching archive.

		"Best" is a somewhat fuzzy concept. In this case, it's assumed to be
		the archive with the largest number of images in common.
		If two archives share the same number of matching images, the larger
		of the two matching archives is selected. If they're the same size,
		the chosen archive will be chosen arbitrarily.

		Returns:
			String: Path to archive on the local filesystem. Path is verified to
				exist at time of return.
		'''
		ret = self.getMatchingArchives()
		return self._getBestMatchingArchive(ret)

	def getBestPhashMatch(self, distance=PHASH_DISTANCE_THRESHOLD):
		'''
		Get the filesystem path of the "best" matching archive.

		"Best" is a somewhat fuzzy concept. In this case, it's assumed to be
		the archive with the largest number of images in common.
		If two archives share the same number of matching images, the larger
		of the two matching archives is selected. If they're the same size,
		the chosen archive will be chosen arbitrarily.

		Identical to `getBestBinaryMatch()`, except including phash-matches
		in the search for matches.

		Returns:
			String: Path to archive on the local filesystem. Path is verified to
				exist at time of return.
		'''
		ret = self.getPhashMatchingArchives(distance)
		return self._getBestMatchingArchive(ret)


	def _shouldSkipFile(self, fileN, fileType):
		'''
		Internal method call. Is used to filter out files that are considered
		"garbage" from evaluation in the matching search. This includes things
		like the windows "Thumbs.db" file, some of the information notes generated
		by the automated ad-removal system in MangaCMS, and `__MACOSX` resource
		fork files&directory that Crapple loves to spew all over any non-HFS
		volumes.

		Returns:
			Boolean: True if the file is garbage, False if it is not.
		'''

		if fileN.endswith("Thumbs.db") and fileType == b'Composite Document File V2 Document, No summary info':
			self.log.info("Windows thumbnail database. Ignoring")
			return True

		if fileN.endswith("deleted.txt") and fileType == b'ASCII text':
			self.log.info("Found removed advert note. Ignoring")
			return True

		if '__MACOSX/' in fileN:
			self.log.info("Mac OS X cache dir. Ignoring")
			return True

		return False
	def _getBestMatchingArchive(self, ret):
		'''
		Internal function that drives `getBestBinaryMatch()` and `getBestPhashMatch()`.

		"Best" match is kind of a fuzzy term here. I define it as the archive with the
		most files in common with the current archive.
		If there are multiple archives with identical numbers of items in common,
		the "best" is then the largest of those files
		(I assume that the largest is probably either a 1. volume archive, or
		2. higher quality)
		'''
		# Short circuit for no matches
		if not len(ret):
			return None

		tmp = {}
		for key in ret.keys():
			tmp.setdefault(len(ret[key]), []).append(key)

		maxKey = max(tmp.keys())

		# If there is only one file with the most items, return that.
		if len(tmp[maxKey]) == 1:
			return tmp[maxKey].pop()

		items = [(os.path.getsize(item), item) for item in tmp[maxKey]]
		items.sort()

		# Finally, sort by size, return the biggest one of them
		return items.pop()[-1]


	def _getBinaryMatchesForHash(self, hexHash, maskedPath):
		matches = {}

		dupsIn = self.db.getOtherHashes(hexHash, fsMaskPath=maskedPath, wantCols=['fsPath', 'internalPath'])
		for fsPath, internalPath in dupsIn:

			isNotMasked =  any([fsPath.startswith(maskedPath) for maskedPath in self.maskedPaths])
			exists = os.path.exists(fsPath)
			if exists and isNotMasked:
				matches.setdefault(fsPath, set()).add(internalPath)

			elif not exists:
				self.log.warn("Item '%s' no longer exists!", fsPath)
				self.db.deleteBasePath(fsPath)

		return matches


	def _getPhashMatchesForPhash(self, phash, maskedPath, searchDistance):
		pass

	def getMatchingArchives(self):
		'''
		This function does two things.

		1. It iterates over all the files in an archive, checking each file for binary uniqueness
			via MD5sums.
		2. Accumulates a list of each file with any files in common with the archive
			this class was instantiated on.

		The return value can be two things:

		If the instantiated archive contains unique items, the return value is
		an empty set (`{}`).

		If the target archive does not contain unique files, the return value is a
		dict of sets, where the key is the filesystem path of each archive containing
		matching items, and the value is a set containing the items that the
		filesystem-path-key has in common with the target archive.

		'''

		self.log.info("Checking if %s contains any unique files.", self.archPath)

		matches = {}
		for fileN, infoDict in self.arch.iterHashes():

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue

			# get a dict->set of the matching items
			matchDict = self._getBinaryMatchesForHash(infoDict['hexHash'], maskedPath=self.archPath)

			if matchDict:
				# If we have matching items, merge them into the matches dict->set
				for key in matchDict.keys():
					matches.setdefault(key, set()).update(matchDict[key])
			else:
				# Short circuit on unique item, since we are only checking if ANY item is unique
				self.log.info("It contains at least one unique file(s).")
				return {}

		self.log.info("It does not contain any unique file(s).")

		return matches


	# This really, /really/ feels like it should be several smaller functions, but I cannot see any nice ways to break it up.
	# It's basically like 3 loops rolled together to reduce processing time and lookups, and there isn't much I can do about that.
	def getPhashMatchingArchives(self, searchDistance=PHASH_DISTANCE_THRESHOLD):
		'''
		This function effectively mirrors the functionality of `getMatchingArchives()`,
		except that it uses phash-duplicates to identify matches as well as
		simple binary equality.
		'''

		self.log.info("Scanning for phash duplicates.")
		matches = {}

		for fileN, infoDict in self.arch.iterHashes():

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue


			if infoDict['pHash'] == None:
				hasDuplicates = False

				self.log.warn("No phash for file '%s'! Wat?", (fileN))
				self.log.warn("Returned pHash: '%s'", (infoDict['pHash']))
				self.log.warn("File size: %s", (len(infoDict['fileCtnt'])))
				self.log.warn("Guessed file type: '%s'", (infoDict['type']))
				self.log.warn("Using binary dup checking for file!")

				dupsIn = self.db.getOtherHashes(infoDict['hexHash'], fsMaskPath=self.archPath)
				for fsPath, internalPath, dummy_itemhash in dupsIn:

					isNotMasked =  any([fsPath.startswith(maskedPath) for maskedPath in self.maskedPaths])
					if os.path.exists(fsPath) and isNotMasked:
						matches.setdefault(fsPath, set()).add(fileN)
						hasDuplicates = True
					elif not isNotMasked:
						pass
						# self.log.info("Match masked by filter: '%s'", fsPath)
					else:
						self.log.warn("Item '%s' no longer exists!", fsPath)
						self.db.deleteBasePath(fsPath)

				self.log.warn("Found binary duplicates!")

			elif infoDict['pHash'] == 0:
				self.log.warning("Skipping any checks for hash value of '%s', as it's uselessly common.", infoDict['pHash'])
				continue
			else:

				proximateFiles = self.db.getWithinDistance(infoDict['pHash'], searchDistance)
				# self.log.info("File: '%s', '%s'. Number of matches %s", self.archPath, fileN, len(proximateFiles))

				hasDuplicates = []

				keys = ["dbid", "fspath", "internalpath", "itemhash", "phash", "dhash", "itemkind", "imgx", "imgy"]
				rows = [dict(zip(keys, row)) for row in proximateFiles]

				# for row in [match for match in proximateFiles if (match and match[1] != self.archPath)]:
				for row in rows:

					# Mask out items on the same path.
					if row['fspath'] == self.archPath:
						continue

					isNotMasked = any([fsPath.startswith(maskedPath) for maskedPath in self.maskedPaths])

					if isNotMasked and os.path.exists(row['fsPath']) :
						matches.setdefault(row['fsPath'], set()).add(fileN)
						hasDuplicates = True
					elif isNotMasked:
						self.log.warn("Item '%s' no longer exists!", row['fsPath'])
						self.db.deleteBasePath(row['fsPath'])

			# Short circuit on unique item, since we are only checking if ANY item is unique

			if not hasDuplicates:
				self.log.info("Archive contains at least one unique phash(es).")
				self.log.info("First unique file: '%s'", fileN)
				return {}

		self.log.info("Archive does not contain any unique phashes.")
		return matches


	def getHashes(self, shouldPhash=True):

		self.log.info("Getting item hashes for %s.", self.archPath)
		ret = []
		for fileN, infoDict in self.arch.iterHashes():

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue

			item = (self.archPath, fileN, infoDict)
			ret.append(item)

		self.log.info("%s Fully hashed.", self.archPath)
		return ret

	def deleteArch(self, moveToPath=False):

		self.db.deleteBasePath(self.archPath)
		if not moveToPath:
			self.log.warning("Deleting archive '%s'", self.archPath)
			os.remove(self.archPath)
		else:
			dst = self.archPath.replace("/", ";")
			dst = os.path.join(moveToPath, dst)
			self.log.info("Moving item from '%s'", self.archPath)
			self.log.info("              to '%s'", dst)
			try:
				shutil.move(self.archPath, dst)
			except KeyboardInterrupt:
				raise
			except OSError:
				self.log.error("ERROR - Could not move file!")
				self.log.error(traceback.format_exc())


	def addNewArch(self):

		self.log.info("Hashing file %s", self.archPath)

		# Delete any existing hashes that collide
		self.db.deleteBasePath(self.archPath)

		# And tell the hasher to process the new archive.
		self.hash.processArchive(self.archPath)


	# Proxy through to the archChecker from UniversalArchiveInterface
	@staticmethod
	def isArchive(archPath):
		return pArch.PhashArchive.isArchive(archPath)



def processDownload(filePath):
	status = ''
	bestMatch = None


	return status, bestMatch
