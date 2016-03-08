

import re

import copy
import settings
import logging
import psycopg2
import time

import threading
import os
import os.path

import unicodedata

import pyinotify

import random
random.seed()

# --------------------------------------------------------------

# Asshole scanlators who don't put their name in "[]"
# Fuck you people. Seriously
shitScanlators = ["rhs", "rh", "mri", "rhn", "se", "rhfk", "mw-rhs"]

chapVolRe     = re.compile(r"(?:(?:ch?|v(?:ol(?:ume)?)?|(?:ep)|(?:stage)|(?:pa?r?t)|(?:chapter)|(?:story)|(?:extra)|(?:load)|(?:log)) ?\d+)", re.IGNORECASE)
trailingNumRe = re.compile(r"(\d+$)", re.IGNORECASE)


# In a lot of situations, we don't have a series name (particularly for IRC downloads, etc...)
# This function tries to clean up filenames enough that we can then match the filename into
# the name database.
# It's crude as hell, but short of a neural net or something, it's as good as it's gonna get
# for fuzzy matching strings into the database.
# Something like levenshtein string distance might be interesting, but I'd be too concerned
# about false-positive matches. Failing to no-match occationally is FAR preferable to
# failing to wrong-match, so we fail no-match.
def guessSeriesFromFilename(inStr):
	inStr = inStr.lower()
	inStr = removeBrackets(inStr)

	# if there is a "." in the last 6 chars, it's probably an extension. remove it.
	if "." in inStr[-6:]:
		inStr, dummy_ext = inStr.rsplit(".", 1)

	# Strip out scanlator name strings for scanlators who are assholes and don't bracket their group name.
	for shitScanlator in shitScanlators:
		if inStr.lower().endswith(shitScanlator.lower()):
			inStr = inStr[:len(shitScanlator)*-1]

	inStr = inStr.replace("+", " ")
	inStr = inStr.replace("_", " ")
	inStr = inStr.replace("the4koma", " ")
	inStr = inStr.replace("4koma", " ")

	inStr = stripChapVol(inStr)

	inStr = inStr.strip()
	inStr = stripTrailingNumbers(inStr)

	inStr = prepFilenameForMatching(inStr)
	return inStr

def stripChapVol(inStr):
	inStr = chapVolRe.sub(" ", inStr)
	return inStr

def stripTrailingNumbers(inStr):
	inStr = trailingNumRe.sub(" ", inStr)
	return inStr

# Execution time of ~ 0.000052889607680 second (52 microseconds)
def prepFilenameForMatching(inStr):
	# inStr = cleanUnicode(inStr)
	inStr = makeFilenameSafe(inStr)
	inStr = sanitizeString(inStr)
	return inStr.lower()

def makeFilenameSafe(inStr):

	# FUCK YOU SMART-QUOTES.
	inStr = inStr.replace("“",  " ") \
				 .replace("”",  " ")

	inStr = inStr.replace("%20", " ") \
				 .replace("<",  " ") \
				 .replace(">",  " ") \
				 .replace(":",  " ") \
				 .replace("\"", " ") \
				 .replace("/",  " ") \
				 .replace("\\", " ") \
				 .replace("|",  " ") \
				 .replace("?",  " ") \
				 .replace("*",  " ") \
				 .replace('"', " ")

	# zero-width space bullshit (goddammit unicode)
	inStr = inStr.replace("\u2009",  " ") \
				 .replace("\u200A",  " ") \
				 .replace("\u200B",  " ") \
				 .replace("\u200C",  " ") \
				 .replace("\u200D",  " ") \
				 .replace("\uFEFF",  " ")

	# Collapse all the repeated spaces down.
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")


	# inStr = inStr.rstrip(".")  # Windows file names can't end in dot. For some reason.
	# Fukkit, disabling. Just run on linux.

	inStr = inStr.rstrip("! ")   # Clean up trailing exclamation points
	inStr = inStr.strip(" ")    # And can't have leading or trailing spaces

	return inStr


# I have a love-hate unicode relationship. I'd /like/ to normalize everything, but doing
# so breaks more then it fixes. Arrrrgh.
def cleanUnicode(inStr):
	return unicodedata.normalize("NFKD", inStr).encode("ascii", errors="replace").decode()


bracketStripRe = re.compile(r"(\[[\+\~\-\!\d\w &:]*\])")

def removeBrackets(inStr):
	inStr = bracketStripRe.sub(" ", inStr)
	while inStr.find("  ")+1:
		inStr = inStr.replace("  ", " ")
	return inStr

# Basically used for dir-path cleaning to prep for matching, and not much else
def sanitizeString(inStr, flatten=True):
	baseName = inStr
	if flatten:
		# Adding "-" processing.
		baseName = baseName.replace("-", " ")
		baseName = baseName.replace("!", " ")

		baseName = baseName.replace("~", "")		 # Spot fixes. We'll see if they break anything
		baseName = baseName.replace(".", "")
		baseName = baseName.replace(";", "")
		baseName = baseName.replace(":", "")
		baseName = baseName.replace("-", "")
		baseName = baseName.replace("?", "")
		baseName = baseName.replace('"', "")
		baseName = baseName.replace("'", "")

	# Bracket stripping has to be done /after/ special chars are cleaned,
	# otherwise, they can break the regex.
	baseName = removeBrackets(baseName)				#clean brackets

	# baseName = baseName.replace("'", "")
	while baseName.find("  ")+1:
		baseName = baseName.replace("  ", " ")

	# baseName = unicodedata.normalize('NFKD', baseName).encode("ascii", errors="ignore")  # This will probably break shit


	return baseName.lower().strip()

def extractRating(inStr):
	# print("ExtractRating = '%s', '%s'" % (inStr, type(inStr)))
	search = re.search(r"^(.*?)\[([~+\-!]+)\](.*?)$", inStr)
	if search:
		# print("Found rating! Prefix = {pre}, rating = {rat}, postfix = {pos}".format(pre=search.group(1), rat=search.group(2), pos=search.group(3)))
		return search.group(1), search.group(2), search.group(3)
	else:
		return inStr, "", ""

def ratingStrToInt(inStr):


	pos = inStr.count("+")
	neg = inStr.count("-")

	return pos - neg

def ratingStrToFloat(inStr):

	pos = inStr.count("+")
	neg = inStr.count("-")
	half = inStr.count("~")

	return (pos - neg) + (half * 0.5)

def extractRatingToFloat(inStr):
	dummy, rating, dummy = extractRating(inStr)
	if not rating:
		return 0
	return ratingStrToFloat(rating)



def floatToRatingStr(newRating):

	# print("Rating change call!")
	newRating, remainder = int(newRating), int((newRating%1)*2)
	if newRating > 0 and newRating <= 5:
		ratingStr = "+"*newRating
	elif newRating == 0:
		ratingStr = ""
	elif newRating < 0 and newRating > -6:
		ratingStr = "-"*abs(newRating)
	else:
		raise ValueError("Invalid rating value: %s!", newRating)
	if remainder:
		ratingStr += "~"

	return ratingStr


def isProbablyImage(fileName):
	imageExtensions = [".jpeg", ".jpg", ".gif", ".png", ".apng", ".svg", ".bmp"]
	fileName = fileName.lower()
	for ext in imageExtensions:
		if fileName.endswith(ext):
			return True

	return False

def extractChapterVol(inStr):

	# Becuase some series have numbers in their title, we need to preferrentially
	# chose numbers preceeded by known "chapter" strings when we're looking for chapter numbers
	# and only fall back to any numbers (chpRe2) if the search-by-prefix has failed.
	chpRe1 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season) ?(?:chapter |ch|c)(?: |_|\.)?(\d+)", re.IGNORECASE)
	chpRe2 = re.compile(r"(?<!volume)(?<!vol)(?<!v)(?<!of)(?<!season) ?(?: |_)(?: |_|\.)?(\d+)", re.IGNORECASE)
	volRe = re.compile(r"(?: |_|\-)(?:volume|vol|v|season)(?: |_|\.)?(\d+)", re.IGNORECASE)

	chap = None
	for chRe in [chpRe1, chpRe2]:
		chapF = chRe.findall(inStr)
		if chapF:
			chap  = float(chapF.pop(0)) if chapF else None
		if chap != None:
			break

	volKey = volRe.findall(inStr)
	vol    = float(volKey.pop(0))  if volKey    else None

	chap   = chap if chap != None else 0.0
	vol    = vol  if vol  != None else 0.0

	return chap, vol



# ------------------------------------------------------


# proxy that makes a DB look like a dict
# Opens a dynamically specifiable database, though the database must be one of a predefined set.
class MtNamesMapWrapper(object):

	log = logging.getLogger("Main.NSLookup")

	modes = {
		"buId->fsName" : {"cols" : ["buId", "fsSafeName"], "table" : 'munamelist',  'failOnMissing' : False},
		"buId->name"   : {"cols" : ["buId", "name"],       "table" : 'munamelist',  'failOnMissing' : False},
		"fsName->buId" : {"cols" : ["fsSafeName", "buId"], "table" : 'munamelist',  'failOnMissing' : False},
		"buId->buName" : {"cols" : ["buId", "buName"],     "table" : 'mangaseries', 'failOnMissing' : False},
		"buName->buId" : {"cols" : ["buName", "buId"],     "table" : 'mangaseries', 'failOnMissing' : False}
	}

	loaded = False
	# special class members that are picked up by the maintenance service, and used to trigger periodic updates from the DB
	# TL;DR magical runtime-introspection bullshit. Basically, if there is an
	# object defined in this file's namespace, with the `NEEDS_REFRESHING` attribute, the houskeeping task
	# will call {object}.refresh() every REFRESH_INTERVAL seconds.
	NEEDS_REFRESHING = True
	REFRESH_INTERVAL = 60*2.5

	# define conn to shut up pylinter
	conn = None
	def __init__(self, mode):


		self.updateLock = threading.Lock()


		self.log.info("Loading NSLookup")

		if not mode in self.modes:
			raise ValueError("Specified mapping mode not valid")
		self.modeKey = mode
		self.mode = self.modes[mode]
		self.openDB()

		self.lastUpdate = 0
		self.lutItems = {}

		self.queryStr = 'SELECT %s FROM %s WHERE %s=%%s;' % (self.mode["cols"][1], self.mode["table"], self.mode["cols"][0])
		self.allQueryStr = 'SELECT %s, %s FROM %s;' % (self.mode["cols"][0], self.mode["cols"][1], self.mode["table"])
		self.log.info("Mode %s, Query %s", mode, self.queryStr)
		self.log.info("Mode %s, IteratorQuery %s",  mode, self.allQueryStr)


	def stop(self):
		self.log.info("Unoading NSLookup")
		self.closeDB()

	def refresh(self):
		self.log.info("Refresh call! for %s mapping cache.", self.modeKey)
		tmp = {}
		for key, buId in self.iteritems():
			key = key.lower()

			if not key in tmp:
				tmp[key] = set([buId])
			else:
				tmp[key].add(buId)

		self.log.info("Refresh call complete. Have %s keys", len(tmp))
		self.lutItems = tmp

	def openDB(self):
		self.log.info( "NSLookup Opening DB...")
		try:
			self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

		# self.conn.autocommit = True
		self.log.info("opened")

		with self.conn.cursor() as cur:
			cur.execute('''SELECT tablename FROM pg_catalog.pg_tables WHERE tablename='%s';''' % self.mode["table"])
			rets = cur.fetchall()

		self.conn.commit()
		if rets:
			rets = rets[0]
		if not self.mode["table"] in rets:   # If the DB doesn't exist, set it up.
			self.log.warning("DB Not setup for %s.", self.mode["table"])
			if self.mode['failOnMissing']:
				raise ValueError
			else:
				# We can't preload the dict, since it doesn't exist, so disable preloading.
				pass

	def closeDB(self):
		self.log.info( "Closing DB...")
		self.conn.close()
		self.log.info( "done")

	def iteritems(self):


		with self.conn.cursor() as cur:
			cur.execute(self.allQueryStr)
			rets = cur.fetchall()

		self.conn.commit()

		for fsSafeName, buId in rets:
			yield fsSafeName, buId


	def __getitem__(self, key):
		if not self.loaded:
			self.loaded = True
			self.refresh()

		# if we have a key filtering function, run the key through it
		if "keyfunc" in self.mode:
			key = self.mode["keyfunc"](key)

		# db is all CITEXT, so we emulate that by calling lower on ALL THE THINGS
		key = key.lower()

		if not key in self.lutItems:
			return []

		# Have to do list comprehension so we don't return the item by reference,
		# which can lead to it getting clobbered.
		return [item for item in self.lutItems[key]]

	def __contains__(self, key):

		if key in self.lutItems[key]:
			return True
		return False




class EventHandler(pyinotify.ProcessEvent):
	def __init__(self, paths):
		super(EventHandler, self).__init__()
		self.paths = {}
		for path in paths:
			self.paths[path] = False
		self.updateLock = threading.Lock()

	def process_default(self, event):
		self.updateLock.acquire()
		# print("Dir monitor detected change!", event)
		for path in self.paths.keys():
			if event.path.startswith(path):
				self.paths[path] |= True
				# print("Changed base-path = ", path)
		# print("Event path?", event.path)
		self.updateLock.release()

	def setPathDirty(self, path):
		print("Setting path '{path}' as dirty".format(path=path))
		self.updateLock.acquire()
		self.paths[path] = True
		self.updateLock.release()

	def getClearChangedStatus(self, path):

		self.updateLock.acquire()
		ret = self.paths[path]
		self.paths[path] = False
		self.updateLock.release()

		return ret


MONITORED_FS_EVENTS = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | \
						pyinotify.IN_MOVED_TO | pyinotify.IN_MOVE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_ATTRIB

# Caching proxy that makes a directories look like a dict.
# Does folder-name mangling to provide case-insensitivity, and provide some
# robusness to minor name variations.
class DirNameProxy(object):

	# Make it a borg class (all instances share state)
	_shared_state = {}

	log = logging.getLogger("Main.DirLookup")

	# test-mode is when the unittesting system pre-loads the dir-dict with known values,
	# so we don't have to start the dir observers (sloooow).
	# Therefore, in test-mode, we don't check if the observers exist.
	testMode = False


	def __init__(self, paths):
		self.__dict__ = self._shared_state

		self.notifierRunning = False
		self.updateLock = threading.Lock()


		self.paths = paths

		self.lastCheck = 0
		self.maxRate = 5
		self._dirDicts = {}


		# for watch in self.


	# special class members that are picked up by the maintenance service, and used to trigger periodic updates from the DB
	# Basically, if there is an object defined in this file's namespace, with the `NEEDS_REFRESHING` attribute, the houskeeping task
	# will call {object}.refresh() every REFRESH_INTERVAL seconds.
	# TL;DR magical runtime-introspection bullshit.
	NEEDS_REFRESHING = True
	REFRESH_INTERVAL = 60


	# define a few things to shut up pylinter
	wm       = None
	eventH   = None
	notifier = None
	def refresh(self):
		self.log.info("Refresh call! for dirMonitor system.")
		self.checkUpdate()
		self.log.info("DirMonitor system refreshed.")

	def observersActive(self):
		return self.notifierRunning

	def startDirObservers(self, useObservers=True):
		# Observers do not need to be started for simple use, particularly
		# for quick-scripts where the filesystem is not expected to change significantly.
		# Pass useObservers=False to avoid the significant delay
		# in allocating directory observers.


		self.notifierRunning = True
		# Used to check that the directories have been loaded.
		# Should probably be broken up into `notifierRunning` and `dirsLoaded` flags.

		if useObservers:
			if not "wm" in self.__dict__:
				self.wm = pyinotify.WatchManager(exclude_filter=lambda p: os.path.isfile(p))
				self.eventH = EventHandler([item["dir"] for item in self.paths.values()])
				self.notifier = pyinotify.ThreadedNotifier(self.wm, self.eventH)

			self.log.info("Setting up filesystem observers")
			for key in self.paths.keys():
				if not "observer" in self.paths[key]:
					self.log.info("Instantiating observer for path %s", self.paths[key]["dir"])

					self.paths[key]["observer"] = self.wm.add_watch(self.paths[key]["dir"], MONITORED_FS_EVENTS, rec=True)


				else:
					self.log.info("WARNING = DirNameProxy Instantiated multiple times!")

			self.notifier.start()
			self.log.info("Filesystem observers initialized")
			self.log.info("Loading DirLookup")
		else:
			self.eventH = EventHandler([item["dir"] for item in self.paths.values()])

		self.checkUpdate(force=True)
		baseDictKeys = list(self._dirDicts.keys())
		baseDictKeys.sort()

	def stop(self):
		# Only stop once (should prevent on-exit errors)
		if self.notifierRunning:
			self.log.info("Unoading DirLookup")
			self.notifier.stop()
			self.notifierRunning = False

	def getDirDict(self, dlPath):

		self.log.info( "Loading Output Dirs for path '%s'...", dlPath)
		if not os.path.exists(dlPath):
			raise ValueError("Download path %s does not exist?" % dlPath)
		targetContents = os.listdir(dlPath)
		targetContents.sort()
		#self.log.info( "targetContents", targetContents)
		targets = {}
		for dirPath in targetContents:
			fullPath = os.path.join(dlPath, dirPath)
			if os.path.isdir(fullPath):
				baseName = getCanonicalMangaUpdatesName(dirPath)
				baseName = prepFilenameForMatching(baseName)

				if baseName in targets:
					print("ERROR - Have muliple entries for directory!")
					print("Current dir = '%s'" % fullPath)
					print("Other   dir = '%s'" % targets[baseName])
					# raise ValueError("Have muliple entries for directory!")

				targets[baseName] = fullPath

			# print("Linking '%s' to '%s'" % (fullPath, baseName))
		self.log.info( "Done")


		return targets

	def manuallyLoadDirDict(self, dirItems):
		tmp = {}
		self.testMode = True
		for name in dirItems:

			baseName = getCanonicalMangaUpdatesName(name)
			baseName = prepFilenameForMatching(baseName)
			tmp[baseName] = name

		self._dirDicts[0] = tmp


	def checkUpdate(self, force=False, skipTime=False):

		updateTime = time.time()
		if not updateTime > (self.lastCheck + self.maxRate) and (not force) and (not skipTime):
			print("DirDicts not stale!")
			return
		self.updateLock.acquire()

		self.lastCheck = updateTime

		keys = list(self.paths.keys())
		keys.sort()
		# print("Keys = ", keys)
		# print("DirNameLookup checking for changes (force=%s)!" % force)

		for key in keys:
			# Only query the filesystem at most once per *n* seconds.
			if updateTime > self.paths[key]["lastScan"] + self.paths[key]["interval"] or force or skipTime:
				changed = self.eventH.getClearChangedStatus( self.paths[key]["dir"])

				if changed or force:
					self.log.info("DirLookupTool updating %s, path=%s!", key, self.paths[key]["dir"])
					self.log.info("DirLookupTool updating from Directory")
					self._dirDicts[key] = self.getDirDict(self.paths[key]["dir"])
					self.paths[key]["lastScan"] = updateTime

		self.updateLock.release()

	# Force the update of the directory containing the passed path dirPath
	# Useful for when programmatic changes are made, such as creating a directory, and
	# you want to force that change to be recognized in the dir proxy immediately.
	# This is needed because the change-watching mechanism doesn't always seem
	# to properly catch folder creation or manipulation.
	# It works great for file changes.
	def forceUpdateContainingPath(self, dirPath):

		self.updateLock.acquire()

		keys = list(self.paths.keys())
		keys.sort()
		for key in keys:
			if self.paths[key]["dir"] in dirPath:
				self.log.info("DirLookupTool updating %s, path=%s!", key, self.paths[key]["dir"])
				self.log.info("DirLookupTool updating from Directory")
				self._dirDicts[key] = self.getDirDict(self.paths[key]["dir"])
				self.paths[key]["lastScan"] = time.time()

		self.updateLock.release()

	def changeRating(self, mangaName, newRating):
		item = self[mangaName]
		if not item['fqPath']:
			raise ValueError("Invalid item")

		print("Item", item)
		print("Path", self.paths[item['sourceDict']]['dir'])
		oldPath = item['fqPath']
		self.changeRatingPath(oldPath, newRating)

	def _checkLookupNewDir(self, fromPath):
		for key in settings.ratingsSort["fromkey"]:
			if fromPath.startswith(settings.mangaFolders[key]["dir"]):
				fromBase = settings.mangaFolders[key]["dir"]
				toBase   = settings.mangaFolders[settings.ratingsSort["tokey"]]["dir"]
				print("Replacing base '%s with base '%s" % (fromBase, toBase))
				return fromPath.replace(fromBase, toBase)

		# If we don't have a directory we want to replace, we just return the string as passed
		return fromPath

	def changeRatingPath(self, oldPath, newRating):

		tmpPath = oldPath
		if hasattr(settings, "ratingsSort"):
			if newRating >= settings.ratingsSort["thresh"]:
					tmpPath = self._checkLookupNewDir(oldPath)

		prefix, dummy_rating, postfix = extractRating(tmpPath)

		if newRating == 0:
			return

		ratingStr = floatToRatingStr(newRating)

		if len(ratingStr):
			ratingStr = " [{rat}] ".format(rat=ratingStr)

		newPath = "{pre}{rat}{pos}".format(pre=prefix, rat=ratingStr, pos=postfix)
		newPath = newPath.rstrip(" ").lstrip(" ")

		# print("Oldpath = ", oldPath)
		# print("Newpath = ", newPath)
		if oldPath != newPath:
			if os.path.exists(newPath):
				raise ValueError("New path exists already!")
			else:
				os.rename(oldPath, newPath)
				if self.notifierRunning:
					self.eventH.setPathDirty(os.path.split(oldPath)[0])
					print("Calling checkUpdate")
					self.checkUpdate(skipTime=True)
					print("checkUpdate Complete")


	def filterPreppedNameThroughDB(self, name):
		if not self.notifierRunning and self.testMode == False:
			self.log.warning("Directory observers not started! No directory contents will have been loaded!")
		name = getCanonicalMangaUpdatesName(name)
		name = prepFilenameForMatching(name)
		return name

	def getPathByKey(self, key):
		return self.paths[key]

	def getDirDicts(self):
		return self._dirDicts

	def getRawDirDict(self, key):
		return self._dirDicts[key]

	def getFromSpecificDict(self, dictKey, itemKey):
		filteredKey = self.filterPreppedNameThroughDB(itemKey)
		if not filteredKey:
			return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": filteredKey, "rating": None, "sourceDict": None}

		# print("ItemKey", itemKey, filteredKey)
		# print("Key = ", dictKey, filteredKey,  filteredKey in self._dirDicts[dictKey])
		if filteredKey in self._dirDicts[dictKey]:
			tmp = self._dirDicts[dictKey][filteredKey]
			return self._processItemIntoRet(tmp, itemKey, filteredKey, dictKey)

		return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": filteredKey, "rating": None, "sourceDict": None}


	def whichDictContainsKey(self, itemKey):
		baseDictKeys = list(self._dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:
			if itemKey in self._dirDicts[dirDictKey]:
				return dirDictKey
		return False

	def iteritems(self):
		# self.checkUpdate()

		baseDictKeys = list(self._dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:
			keys = list(self._dirDicts[dirDictKey].keys())  # I want the items sorted by name, so we have to sort the list of keys, and then iterate over that.
			keys.sort()

			for key in keys:
				item = self[key]

				# Inject the key we're iterating from, so we can see if we're fetching an item from a different/the wrong dict
				# when doing the actual lookup
				item['iterKey'] = dirDictKey
				yield key, item

	def _processItemIntoRet(self, item, origKey, filteredKey, dirDictKey):
		dummy_basePath, dirName = os.path.split(item)
		dummy_prefix, rating, dummy_postfix = extractRating(dirName)
		ret = {"fqPath" : item, "item": dirName, "inKey" : origKey, "dirKey": filteredKey, "rating": rating, "sourceDict": dirDictKey}
		return ret

	def getTotalItems(self):
		items = 0
		for item in self._dirDicts.values():
			items += len(item)
		return items

	def random(self):
		items = self.getTotalItems()

		# Special-case for no items, return nothing.
		if items == 0:
			return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": 'None', "rating": None, "sourceDict": None}
		index = random.randint(0, items-1)
		# print("Getting random item with indice", index)
		return self.getByIndex(index)

	def getByIndex(self, index):
		if index < 0 or index >= self.getTotalItems():
			raise ValueError("Index value exceeds allowable range - %s" % index)
		for dummy_key, itemSet in self._dirDicts.items():
			if index >= len(itemSet):
				index -= len(itemSet)
				continue
			else:
				item = itemSet[list(itemSet.keys())[index]]
				dummy_basePath, dirName = os.path.split(item)
				# print("Selected item with dirPath: ", item)
				filteredKey = prepFilenameForMatching(dirName)
				return self[filteredKey]
		raise ValueError("Exceeded valid range?")

	def __getitem__(self, key):
		# self.checkUpdate()
		if len(key.strip()) == 0:
			return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": key, "rating": None, "sourceDict": None}

		filteredKey = self.filterPreppedNameThroughDB(key)
		if not filteredKey:
			return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": filteredKey, "rating": None, "sourceDict": None}

		baseDictKeys = list(self._dirDicts.keys())
		baseDictKeys.sort()


		for dirDictKey in baseDictKeys:
			if filteredKey in self._dirDicts[dirDictKey]:
				tmp = self._dirDicts[dirDictKey][filteredKey]
				return self._processItemIntoRet(tmp, key, filteredKey, dirDictKey)

		return {"fqPath" : None, "item": None, "inKey" : key, "dirKey": filteredKey, "rating": None}

	def __contains__(self, key):
		# self.checkUpdate()

		key = self.filterPreppedNameThroughDB(key)

		if not key:
			return {"fqPath" : None, "item": None, "inKey" : None, "dirKey": key, "rating": None, "sourceDict": None}

		baseDictKeys = list(self._dirDicts.keys())
		baseDictKeys.sort()
		for dirDictKey in baseDictKeys:

			# Limit scanned items to < 100
			if dirDictKey > 99:
				continue

			if key in self._dirDicts[dirDictKey]:
				return key in self._dirDicts[dirDictKey]

		return False

	def __len__(self):
		ret = 0
		for dirDictKey in self._dirDicts.keys():
			ret += len(self._dirDicts[dirDictKey])
		return ret



## If we have the series name in the synonym database, look it up there, and use the ID
## to fetch the proper name from the MangaUpdates database
def getCanonicalMangaUpdatesName(sourceSeriesName):

	mId = getMangaUpdatesId(sourceSeriesName)
	canon = getCanonNameByMuId(mId)
	if canon:
		return canon
	return sourceSeriesName

muIdRegex = re.compile(r'\[MuId (\d+)\]')

## If we have the series name in the synonym database, look it up there, and use the ID
## to fetch the proper name from the MangaUpdates database
def getMangaUpdatesId(sourceSeriesName):

	# Allow the Id Override tag in the dirname to hard-code the Id.
	idS = muIdRegex.search(sourceSeriesName)
	if idS:
		return idS.group(1)

	fsName = prepFilenameForMatching(sourceSeriesName)
	if not fsName:
		return False

	mId = buIdLookup[fsName]
	if mId and len(mId) == 1:
		return mId.pop()
	return False


def getCanonNameByMuId(muId):

	if muId:
		correctSeriesName = idLookup[muId]
		if correctSeriesName and len(correctSeriesName) == 1:
			return correctSeriesName.pop()
	return None

def getAllMangaUpdatesIds(sourceSeriesName):

	fsName = prepFilenameForMatching(sourceSeriesName)
	if not fsName:
		return False

	mId = buIdLookup[fsName]
	return mId




## If we have the series name in the synonym database, look it up there, and use the ID
## to fetch the proper name from the MangaUpdates database
def haveCanonicalMangaUpdatesName(sourceSeriesName):

	mId = getMangaUpdatesId(sourceSeriesName)

	if mId:
		return True
	# mId = buIdFromName[sourceSeriesName]
	# if mId and len(mId) == 1:
	# 	return True
	return False


buIdLookup       = MtNamesMapWrapper("fsName->buId")
buSynonymsLookup = MtNamesMapWrapper("buId->name")
idLookup         = MtNamesMapWrapper("buId->buName")
buIdFromName     = MtNamesMapWrapper("buName->buId")

dirNameProxy     = DirNameProxy(settings.mangaFolders)




def testNameTools():
	import unittest


	class TestSequenceFunctions(unittest.TestCase):

		def setUp(self):
			dirNameProxy.startDirObservers()

		def test_name_001(self):
			self.assertTrue("Danshi Koukousei no Nichijou" in dirNameProxy)




	unittest.main()


