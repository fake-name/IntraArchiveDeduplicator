

import time
from UniversalArchiveInterface import ArchiveReader
import logging

from natsort import natsorted

# This manages allocating file-handles for web-interface sessions. Each session gets one
# ViewerSession() object, which it can use to view files when told to do so by
# accessing various reader pages.
# The ViewerSession() objects are then managed by the SessionPoolManager(), which
# is owned by the web-server, and of which there (should) only be one.
# there is some borg-class stuff going on to make SessionPoolManager() share
# it's state across all threads (probably an issue if I was concerned much about
# scaling up, but I'm not, so it's not)

class ViewerSession(object):

	archFiles = None
	items     = None
	def __init__(self):
		self.archHandle = None
		self.lastAccess = time.time()

		self.pruneAge = 60*120		 # in Seconds, prune if no access for 120 minutes

	def shouldPrune(self):
		lastChange = time.time() - self.lastAccess
		if lastChange > self.pruneAge:
			return True
		else:
			return False

	def checkOpenArchive(self, archPath):
		if not self.archHandle or self.archHandle.archPath != archPath:
			self.archHandle = ArchiveReader(archPath)
			self.buildImageLookupDict()

		self.lastAccess = time.time()


	def getItemByInternalPath(self, internalPath):
		itemContent = self.archHandle.open(internalPath)
		return itemContent, internalPath


	def __del__(self):
		if self.archHandle:
			del self.archHandle

# There are some subtle race conditions here (a cookie item being deleted after it's checked to
# exist, before it's subsequentially accessed). I'm ignoring them at the moment.

class SessionPoolManager(object):

	# Make it a borg class (all instances share state)
	_shared_state = {}

	max_sessions = 20
	lastSession = 0
	sessions = {}

	log = logging.getLogger("Main.SessionMgr")

	def __init__(self):
		self.__dict__ = self._shared_state


	def __getitem__(self, key):
		if key not in self.sessions:
			self.sessions[key] = ViewerSession()
		return self.sessions[key]

	def __contains__(self, key):
		return key in self.sessions


	def prune(self):
		self.log.info("Checking if any of %s session cookies need to be pruned due to age", len(self.sessions))
		for key in list(self.sessions.keys()):
			if self.sessions[key].shouldPrune():
				self.log.info("Pruning stale session with ID %s", key)
				try:
					self.sessions.pop(key)
				except KeyError:
					self.log.error("Failed to prune session?")
					self.log.error("Current sessions:")
					for key, session in self.sessions.items():
						self.log.error("	'{key}' -> '{sess}'".format(key=key, sess=session))
		if len(self.sessions) > self.max_sessions:
			self.log.info("Need to prune sessions due to session limits")
			sessionList = [(val.lastAccess, key) for key, val in self.sessions.items()]
			sessionList.sort()
			while len(sessionList) > self.max_sessions:
				dummy_acces, delSession = sessionList.pop(0)
				self.log.info("Pruning oldest session with ID %s", delSession)
				self.sessions.pop(delSession)


