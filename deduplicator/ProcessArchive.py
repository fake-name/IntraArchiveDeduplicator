


import pArch
import os
import sys
import os.path
import logging
import time
import pprint
import shutil
import traceback

import dbPhashApi as dbApi

import multiprocessing
import scanner.fileHasher

PHASH_DISTANCE_THRESHOLD = 2

BAD_PHASHES = [
	# Phash value of '0' is commonly a result of an image where there is no content, such as a blank page.
	# There are 79 THOUSAND of these in my collection. As a result, the existence check is prohibitively slow, so
	# we just short-circuit and ignore it.
	                 0,

	-24019198012642646,
]

class ArchiveProcessorException(Exception):
	pass

class DatabaseDesynchronizedError(ArchiveProcessorException):
	pass

class InvalidArchiveContentsException(ArchiveProcessorException):
	pass

class InvalidArchivePhashContentsException(InvalidArchiveContentsException):
	pass

class InvalidArchiveMd5ContentsException(InvalidArchiveContentsException):
	pass

class ProxyDbBase(object):
	def __init__(self):
		self.db = self.getDbConnection()

	# Overridden in child classes so the unit tests can redirect
	# db access to the testing database by returning a different DB
	# connection object.
	def getDbConnection(self):  # pragma: no cover
		return dbApi.PhashDbApi()

	# def convertDbIdToPath(self, inId):
	# 	return self.db.getItem(wantCols=['fsPath', "internalPath"], dbId=inId)


class ArchChecker(ProxyDbBase):
	'''
	Class to encapsulate the required object to check if `archpath` is unique.

	'''

	hasher = scanner.fileHasher.HashThread

	def __init__(self, archPath, pathFilter=None):
		'''
		Params:
			pathFilter (list): default =``['']``
				Basically, if you pass a list of valid path prefixes, any matches not
				on any of those path prefixes are not matched.
				Default is [''], which matches every path, because "anything".startswith('') is true
		'''

		super().__init__()
		self.maskedPaths = pathFilter or ['']

		self.archPath    = archPath
		self.arch        = pArch.PhashArchive(archPath)

		self.log = logging.getLogger("Main.Deduper")
		self.log.info("ArchChecker Instantiated on '%s'", archPath)

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

	def isPhashUnique(self, searchDistance=None):
		'''
		Is the archive this class was instantiated on phash unique, where the
		duplicating files elsewhere on the filesystem still exist.

		Phash-unique means there are matches for each of the files in the archive,
		including searching by phash within distance `searchDistance` for any files
		that are images.

		Returns:
			Boolean: True if unique, False if not.
		'''

		if searchDistance == None:
			searchDistance=PHASH_DISTANCE_THRESHOLD

		ret = self.getPhashMatchingArchives(searchDistance, getAllCommon=False)

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
				If the current archive contains unique files, this will return a empty string.
		'''
		ret = self.getMatchingArchives()
		return self._getBestMatchingArchive(ret)

	def getBestPhashMatch(self, distance=None):
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
		if distance == None:
			distance=PHASH_DISTANCE_THRESHOLD

		ret = self.getPhashMatchingArchives(distance, getAllCommon=False)
		return self._getBestMatchingArchive(ret)

	def getSignificantlySimilarArches(self, searchDistance=None):
		'''
		This function returns a dict of lists containing archives with files in common with
		the current archive. It only operates using phash similarity metrics (as phash searches
		are intrinsically a superset of binary match similarity metrics).

		The dict keys are the number of files in common, and the list is a number of filesystem-
		paths to the intersecting archives.

		'''
		if searchDistance == None:
			searchDistance=PHASH_DISTANCE_THRESHOLD

		common = self.getPhashMatchingArchives(getAllCommon=True, searchDistance=searchDistance)

		ret = self._processMatchesIntoRet(common)

		# Now, we truncate the return common set to every item which has >
		# the mean number of items in common
		# This is a preventative measure against things like scanlators which
		# have a credit page they put EVERYWHERE, and we therefor want to
		# disregard.

		print("Common:")
		pprint.pprint(common)
		print("Ret:")
		pprint.pprint(ret)

		keys = list(ret.keys())
		if not keys:
			return ret

		mean = (sum(keys) / len(keys))
		for key in [key for key in keys if key < mean]:
			ret.pop(key)

		# And pop all items which have only one item in common
		if 1 in ret:
			ret.pop(1)
		return ret

	def _processMatchesIntoRet(self, matches):
		'''
		This takes a dict of items where each key is a filesystem path, and the value
		is a set of internal-paths that are matched in the archive at the key filesystem path.

		It transforms that dict into another dict where the key is the number of matches
		that a filesystem path has, and the value is a list of filesystem paths that
		had `key` matches.
		'''
		ret = {}
		for key in matches.keys():
			ret.setdefault(len(matches[key]), []).append(key)

		# Make the return ordering deterministic
		for key in ret.keys():
			ret[key].sort()
		return ret

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

		thumbs_file_types = [
			# So debian wheezy is so out of date their libmagick
			# doesn't appear to have the mimetype parameter.
			'Composite Document File V2 Document, No summary info',
			'application/CDFV2-corrupt',
			'application/CDFV2',
		]

		if fileN.endswith("Thumbs.db") and fileType in thumbs_file_types:
			self.log.info("Windows thumbnail database. Ignoring")
			return True

		# We have to match both 'ASCII text', and the occational 'ASCII text, with no line terminators'
		if fileN.endswith("deleted.txt") and fileType =='text/plain':
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

		# TODO: The fitness of the match should additionally consider the number of files in each dir.
		#       e.g. if the current file has 100 files, with 10 in common with another file with
		#       100 files, that's not really a good match. On the other hand, if the current
		#       file has 100 files, with 10 in common with another file which has a total of
		#       10 files in it, it's an excellent match since the current file is a complete
		#       superset of the other file.

		# Finally, sort by size, return the biggest one of them
		return items.pop()[-1]


	def _getBinaryMatchesForHash(self, hexHash):
		'''
		Params:
			hexHash (String): The hash to match against.

		Returns:
			dict of sets. Dict keys are filesystem paths, and the set contains
				the internal path of each item in the key that has the query key


		This function searches for all items with a binary hash of `hexHash`, masks out
		any paths in `self.maskedPaths`, and then checks for file existence. If the file exists,
		it's inserted into a local dictionary with the key being the filesystem path,
		and the value being a set into which the internal path is inserted.

		'''
		matches = {}

		dupsIn = self.db.getByHash(hexHash, wantCols=['fsPath', 'internalPath'])
		for fsPath, internalPath in dupsIn:

			# Mask out items on the same path.
			if fsPath == self.archPath:
				continue

			isNotMasked =  any([fsPath.startswith(maskedPath) for maskedPath in self.maskedPaths])
			exists = os.path.exists(fsPath)
			if exists and isNotMasked:
				matches.setdefault(fsPath, set()).add(internalPath)

			elif not exists:
				self.log.warn("Item '%s' no longer exists!", fsPath)
				self.db.deleteDbRows(fspath=fsPath)


		return matches


	def _getPhashMatchesForPhash(self, phash, imgDims, searchDistance):
		'''
		Params:
			phash (integer): The phash to match against.
			searchDistance (integer): The phash search distance.

		Returns:
			dict of sets: Dict keys are filesystem paths, and the set contains
				the internal path of each item that is `searchDistance` or less
				away from `phash`


		This function searches for all items within `searchDistance` of `phash`, masks out
		any paths in `self.maskedPaths`, and then checks for file existence. If the file exists,
		it's inserted into a local dictionary with the key being the filesystem path,
		and the value being a set into which the internal path is inserted.

		'''


		srcX, srcY = imgDims

		matches = {}

		proximateFiles = self.db.getWithinDistance(phash, searchDistance)

		# Pack returned row tuples into nice dicts for easy access
		keys = ["dbid", "fspath", "internalpath", "itemhash", "phash", "itemkind", "imgx", "imgy"]
		rows = [dict(zip(keys, row)) for row in proximateFiles]

		# Filter returned scan results by the maskedPaths context
		# This is done early-on, so we don't get extraPath garbage
		# when the actual scan is done.
		rows = [row for row in rows if any([row['fspath'].startswith(maskedPath) for maskedPath in self.maskedPaths])]


		# for row in [match for match in proximateFiles if (match and match[1] != self.archPath)]:

		if len(rows) > 100:
			self.log.info("Skipping existence check due to quantity of candidate matches.")

		for row in rows:

			# Mask out items on the same path.
			if row['fspath'] == self.archPath:
				continue

			# I genuinely cannot see how this line would get hit, but whatever.
			if row['phash'] == None:      #pragma: no cover
				raise ValueError("Line is missing phash, yet in phash database? DbId = '%s'", row['dbid'])

			if not row['imgx'] or not row['imgy']:
				self.log.warn("Image with no resolution stats! Wat?.")
				self.log.warn("Image: '%s', '%s'", row['fspath'], row['internalpath'])
				continue

			if srcX > row['imgx'] or srcY > row['imgy']:
				# self.log.info("Filtering phash match due to lower resolution.")
				continue


			# If we had more then 100 returnd matches, skip the existence check as
			# it'll take too long, and it's probably safe to assume that /some/ of
			# the found matches exist..
			if len(rows) > 100 or os.path.exists(row['fspath']) :
				matches.setdefault(row['fspath'], set()).add(row['internalpath'])

			else:
				self.log.warn("Item '%s' no longer exists!", row['fspath'])
				self.db.deleteDbRows(fspath=row['fspath'])


		return matches

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

		self.log.info("Checking if %s contains any binary unique files.", self.archPath)

		matches = {}
		for fileN, infoDict in self.arch.iterHashes():

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue

			# get a dict->set of the matching items
			matchDict = self._getBinaryMatchesForHash(infoDict['hexHash'])

			if matchDict:
				# If we have matching items, merge them into the matches dict->set
				for key in matchDict.keys():
					matches.setdefault(key, set()).update(matchDict[key])
			else:
				# Short circuit on unique item, since we are only checking if ANY item is unique
				self.log.info("It contains at least one unique file(s).")
				return {}

		self.log.info("It does not contain any binary unique file(s).")

		return matches

	def _loadFileContents(self):

		ret = []

		for fileN, infoDict in self.arch.iterHashes():

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue

			ret.append((fileN, infoDict))

		return ret

	def _doRowLookup(self, matchids, resolution):

		keys = ["dbid", "fspath", "internalpath", "itemhash", "phash", "itemkind", "imgx", "imgy"]



		ret_rows = []
		for matchid in matchids:



			row = self.db.getItem(dbId=matchid)
			# Sometimes a row has been deleted without being removed from the tree.
			# If this has happened, getItem() will return an empty list.
			# Don't return that, if it happens
			if not row:
				self.log.info("Row deleted without updating tree")
				continue

			row = dict(zip(keys, row))

			# Mask out items on the same path.
			if row['fspath'] == self.archPath:
				continue

			# I genuinely cannot see how this line would get hit, but whatever.
			if row['phash'] is None and resolution:      #pragma: no cover
				raise ValueError("Line is missing phash, yet in phash database? DbId = '%s'", row['dbid'])

			if (not row['imgx'] or not row['imgy']) and resolution:
				self.log.warning("Image with no resolution stats! Wat?.")
				self.log.warning("Image: '%s', '%s'", row['fspath'], row['internalpath'])
				continue


			if resolution and len(resolution) == 2 and ():
				continue

			if resolution and len(resolution) == 2:
				res_x, res_y = resolution
				if res_x > row['imgx'] or res_y > row['imgy']:
					continue

			if not os.path.exists(row['fspath']):
				self.log.info("File deleted without updating tree")
				continue


			ret_rows.append(row)

		# Pack returned row tuples into nice dicts for easy access

		return ret_rows

	def _isBadPee(self, phash):
		return phash in BAD_PHASHES

	def _doHashSearches(self, filelist, searchDistance, getAllCommon):
		for fileN, infoDict in filelist:
			infoDict["fileN"] = fileN

		# Do the normal binary lookup
		for dummy_fileN, infoDict in filelist:
			# get a dict->set of the matching items
			infoDict['binMatchIds'] = [tmp for tmp, in self.db.getByHash(infoDict['hexHash'], wantCols=['dbid'])]

		# Then, atomically do the phash searches
		# I really don't like reaching into the class this far, but
		# it means I don't need to import the contextlib library into the phashdbapi file.

		matches = self.db.searchPhashSet([infoDict['pHash'] for fileN, infoDict in filelist if infoDict['pHash'] is not None], searchDistance)

		for fileN, infoDict in filelist:
			if infoDict['pHash'] is not None:
				infoDict['pMatchIds'] = matches[infoDict['pHash']]

		# print("Data:")
		# print(infoDict)

		# Finally, resolve out the row returns from the p-hash searches out
		# too db rows.
		for fileN, infoDict in filelist:
			if getAllCommon:
				imgDims = None
			else:
				imgDims = (infoDict['imX'], infoDict['imY'])
			# print("Searcing for imgDims: ", imgDims)
			if 'pMatchIds' in infoDict:
				if self._isBadPee(infoDict['pHash']):
					self.log.warning("Skipping any checks for hash value of '%s', as it's uselessly common.", infoDict['pHash'])
				elif len(infoDict['pMatchIds']) > 100:
					self.log.info("Skipping existence check due to quantity of candidate matches.")
				else:
					infoDict['pMatches'] = self._doRowLookup(infoDict['pMatchIds'], imgDims)
					# print("PHash Matches: ", infoDict['pMatches'])

			if 'binMatchIds' in infoDict:
				if self._isBadPee(infoDict['pHash']):
					self.log.warning("Skipping any checks for hash value of '%s', as it's uselessly common.", infoDict['pHash'])
				elif len(infoDict['binMatchIds']) > 100:
					self.log.info("Skipping existence check due to quantity of candidate matches.")
				else:
					infoDict['bMatches'] = self._doRowLookup(infoDict['binMatchIds'], False)
					# print("Binary Matches: ", infoDict['bMatches'])
		return [infoDict for fileN, infoDict in filelist]

	def _checkHashesOk(self, fileContent, searchDistance):
		'''
		Do some integrity checks against the loaded file content, to catch some possible
		issues.

		Primarily, this detects issues where the files in an archive are mis-hashed due to
		library issues.

		The idea is that a single archive should be at least ~75% unique. If an archive has
		10 images, yet only 5 of them are unique even within the archive, something is
		probably wrong somewhere.
		'''

		md5s = [filed['hexHash'] for filen, filed in fileContent if not filed['pHash']]

		muniqueratio = len(set(md5s)) / max(1, len(md5s))
		phashes = [filed['pHash'] for filen, filed in fileContent if filed['pHash']]

		so_far = []
		unique = 0
		for phash in phashes:
			similarity = [dbApi.hammingDistance(phash, other) for other in so_far]
			coincides = [tmp for tmp in similarity if tmp <= searchDistance]
			so_far.append(phash)
			if not coincides:
				unique += 1

		puniqratio = unique / max(1, len(phashes))


		hashratio = len(phashes) / max(1, len(md5s))

		# print("phashes", len(phashes))
		# print("muniqueratio", muniqueratio)
		# print("unique", unique)
		# print("puniqratio", puniqratio)
		# print("hashratio", hashratio)
		# print("len(md5s)", len(md5s))
		# print("len(set(md5s))", len(set(md5s)))

		if len(phashes) and puniqratio < 0.5:
			raise InvalidArchivePhashContentsException("Too many identical images (phash-search) in the archive!")

		# If there are any md5-only files, check they're at least 50% unique
		# Only do this if there are more md5s then images
		if len(md5s) and muniqueratio <= 0.6 and hashratio <= 1:
			raise InvalidArchiveMd5ContentsException("Too many identical files in the archive!")

	# This really, /really/ feels like it should be several smaller functions, but I cannot see any nice ways to break it up.
	# It's basically like 3 loops rolled together to reduce processing time and lookups, and there isn't much I can do about that.
	def getPhashMatchingArchives(self, searchDistance=None, getAllCommon=False):
		'''
		This function effectively mirrors the functionality of `getMatchingArchives()`,
		except that it uses phash-duplicates to identify matches as well as
		simple binary equality.

		The additional `getAllCommon` parameter overrides the early-return behaviour if
		one of the scanned items is unique. As such, if `getAllCommon` is True,
		it will phash search for every item in the archive, even if they're all unique.
		It also disables the resolution filtering of the match results.
		This is necessary for finding commonalities between archives, which is intended
		to return archives that the current archive has potentially superceded.

		'''

		if searchDistance == None:
			searchDistance = PHASH_DISTANCE_THRESHOLD

		self.log.info("Scanning for phash duplicates.")
		matches = {}


		fc = self._loadFileContents()

		# self._checkHashesOk(fc, searchDistance)

		hashMatches = self._doHashSearches(fc, searchDistance, getAllCommon)

		# print("Matches: ", type(hashMatches))
		# print("Match1: ", type(hashMatches[0]))


		for infoDict in hashMatches:
			fileN = infoDict['fileN']

			if self._shouldSkipFile(fileN, infoDict['type']):
				continue


			# Handle cases where an internal file is not an image
			if infoDict['pHash'] is None:
				self.log.warning("No phash for file '%s'! Wat?", fileN)
				self.log.warning("Returned pHash: '%s'", infoDict['pHash'])
				self.log.warning("Guessed file type: '%s'", infoDict['type'])
				self.log.warning("Should skip: '%s'", self._shouldSkipFile(fileN, infoDict['type']))
				self.log.warning("Using binary dup checking for file!")


				# If we have a phash, and yet pMatches is not present,
				# the duper skipped loading the matching files because
				# of quantity.
				# As such, just continue on.
				if 'binMatchIds' in infoDict and not 'bMatches' in infoDict:
					continue

				# get a dict->set of the matching items
				matchList = infoDict['bMatches']

				if matchList:
					for matchDict in matchList:
						# If we have matching items, merge them into the matches dict->set
						matches.setdefault(matchDict['fspath'], set()).add(matchDict['internalpath'])

				elif not getAllCommon:
					# Short circuit on unique item, since we are only checking if ANY item is unique
					self.log.info("It contains at least one unique file(s).")
					return {}


			# Any non-none and non-0 matches get the normal lookup behaviour.
			else:
				# If we have a phash, and yet pMatches is not present,
				# the duper skipped loading the matching files because
				# of quantity.
				# As such, just continue on.
				if 'pHash' in infoDict and 'pMatchIds' in infoDict and not 'pMatches' in infoDict:
					continue

				matchList = infoDict['pMatches']
				if matchList:
					for matchDict in matchList:
						# If we have matching items, merge them into the matches dict->set
						matches.setdefault(matchDict['fspath'], set()).add(matchDict['internalpath'])

				elif not getAllCommon:
					# Short circuit on unique item, since we are only checking if ANY item is unique
					self.log.info("It contains at least one unique file(s).")
					self.log.info("Archive contains at least one unique phash(es).")
					self.log.info("First unique file: '%s'", fileN)
					return {}


		self.log.info("Archive does not contain any unique phashes.")
		return matches


	def deleteArch(self, moveToPath=False):
		'''
		Delete target arch.

		If ``moveToPath`` is specified, the archive will be moved there instead, as an option
		for deferred deletion.

		When ``moveToPath`` is specified, the current path is prepended to the filename, by
		replacing all directory delimiters (``/``) with semicolons (``;``). This allows the
		moved archive to be returned to it's original fs location in (almost) all cases.

		'''
		self.db.deleteDbRows(fspath=self.archPath)
		if not moveToPath:
			self.log.warning("Deleting archive '%s'", self.archPath)
			os.remove(self.archPath)
		else:
			dst = self.archPath.replace("/", ";")
			dst = os.path.join(moveToPath, dst)
			self.log.info("Moving item from '%s'", self.archPath)
			self.log.info("              to '%s'", dst)
			try:
				for x in range(3):
					try:
						shutil.move(self.archPath, dst)
						break
					except OSError:
						self.log.error("Failure moving file?")
						time.sleep(0.1)
						if x == 2:
							raise
			except KeyboardInterrupt:  # pragma: no cover  (Can't really test keyboard interrupts)
				raise
			except (OSError, FileNotFoundError):
				self.log.error("ERROR - Could not move file!")
				self.log.error(traceback.format_exc())


	def deleteArchFromDb(self):

		self.db.deleteDbRows(fspath=self.archPath)


	def addArch(self):
		'''
		Add the hash values from the target archive to the database, with the current
		archive FS path as it's location.
		'''

		self.log.info("Adding archive to database. Hashing file: %s", self.archPath)

		# Delete any existing hashes that collide
		self.deleteArchFromDb()

		# And tell the hasher to process the new archive.
		hasher = self.hasher(inputQueue=None, outputQueue=None, runMgr=None)

		hasher.processArchive(self.archPath)


	# Proxy through to the archChecker from UniversalArchiveInterface
	@staticmethod
	def isArchive(archPath):
		'''
		Simple staticmethod boolean check. Used to determine of the item
		at the passed path (``archPath``) is actually an archive, by
		looking at it with ``libmagic``.
		'''
		return pArch.PhashArchive.isArchive(archPath)



def getSignificantlySimilarArches(filePath, distance=4):
	log = logging.getLogger("Main.DedupServer")
	# print("Args:", (filePath, distance))
	status = ''
	bestMatch = None
	common = {}
	try:
		ck = ArchChecker(filePath)

		return ck.getSignificantlySimilarArches(searchDistance=distance)

	except Exception:
		log.critical("Exception when processing item!")
		for line in traceback.format_exc().split("\n"):
			log.critical(line)
		return "error!"





def processDownload(filePath, pathFilter=None, distance=None, moveToPath=None, checkClass=ArchChecker, cross_match=True):
	'''
	Process the file `filePath`. If it's a phash or binary duplicate, it is deleted.

	The `checkClass` param is to allow the checking class to be overridden for testing.

	Returns:
		(tag, bestMatch) tuple.
			`tag` is a string containing space-separated tags corresponding to
				the deduplication state (e.g. `deleted`, `was-duplicate`, and `phash-duplicate`)
			`bestMatch` is the fspath of the best-matching other archive.
	'''
	log = logging.getLogger("Main.DedupServer")

	status = ''
	bestMatch = None
	common = {}
	try:
		ck = checkClass(filePath, pathFilter=pathFilter)

		if cross_match:
			common = ck.getSignificantlySimilarArches(searchDistance=distance)
		else:
			common = None

		binMatch = ck.getBestBinaryMatch()
		if binMatch:
			ck.deleteArch(moveToPath=moveToPath)
			return 'deleted was-duplicate', binMatch, common

		pMatch = ck.getBestPhashMatch(distance=distance)
		if pMatch:
			ck.deleteArch(moveToPath=moveToPath)
			return 'deleted was-duplicate phash-duplicate', pMatch, common

		ck.addArch()


	except Exception:
		log.critical("Exception when processing item!")
		for line in traceback.format_exc().split("\n"):
			log.critical(line)
		status += " damaged"
	status = status.strip()

	log.info("Returning status '%s' for archive '%s'. Best Match: '%s'", status, filePath, bestMatch)

	return status, bestMatch, common



def commandLineReloadTree(scanConf):
	import rpyc
	remote = rpyc.connect("localhost", 12345)
	# print("Forcing reload of phash tree. Search functionality will block untill load is complete.")
	remote.root.reloadTree()
	# print("Tree reloaded!")

def commandLineProcess(scanConf):
	import scanner.logSetup
	import rpyc

	scanner.logSetup.initLogging()

	if not os.path.exists(scanConf.sourcePath):
		# print("ERROR: Source file does not exist!")
		return
	if not os.path.isfile(scanConf.sourcePath):
		# print("ERROR: Source is not a file!")
		return

	if scanConf.noContext:
		scanContext = None
	else:
		scanContext = [os.path.split(scanConf.sourcePath)]

	remote = rpyc.connect("localhost", 12345)

	status, bestMatch, intersections = remote.root.processDownload(
		scanConf.sourcePath,
		pathFilter=scanContext,
		distance=6,
		moveToPath=None,
		locked=True)
	# print("Processed archive. Return status '%s'", status)
	if bestMatch:
		print("Matching archive '%s'", bestMatch)
	return status, bestMatch, intersections

