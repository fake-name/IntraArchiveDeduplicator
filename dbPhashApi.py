#!/usr/bin/python
# -*- coding: utf-8 -*-

import dbApi
import collections
import gc

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb
import traceback
import server.decorators

@server.decorators.Singleton
class TreeProxy(hamDb.BkHammingTree):
	pass

'''
The idea here is that we have a child-class of DbApi that makes it /look/ like we can query PostgreSQL
for phash-related things, and which simply intercepts all phash search related calls, and looks them up
itself, in it's internal data-structures. Any calls that modify or update the phash data-sets should be
replayed onto the internal BK tree.

The Tree is loaded from the database when the class is first instantiated, and then maintained as an
in-memory database for the life of the program. The BK-tree is a singleton, which should be thread-safe, so
it's being shared across multiple connections should not be an issue.

The BK-tree being a singleton is done for memory reasons. With ~12M tree items, the BKtree requires about 5 GB
of memory, and takes about 45 seconds to load from posrgresql. As such, having a tree-per-connection would
be prohibitive for memory reasons, and each connection would be extremely slow to start.

Because any changes to the database are committed to Postgres immediately, and then the corresponding
update is simply performed on the BK tree, the BK tree should always be fully up to date with the contents
of the postgres database, so it /shouldn't/ need to be reloaded periodically or anything (we'll see).

The tree reload facility is mostly intended for refreshing the tree when the db has been changed by
external tools, such as the hash scanner.
'''

def hammingDistance(v1, v2):
	return hamDb.hamming_dist(v1, v2)

class PhashDbApi(dbApi.DbApi):

	# Read in phash/dbId values in chunks of 50K rows
	streamChunkSize = 50000

	def __init__(self, noglobal=False):
		super().__init__()

		if noglobal:
			self.tree = hamDb.BkHammingTree()
		else:
			self.tree = TreeProxy.Instance()

		assert self.tree is not None
		# Only load the tree if it's empty

		# with self.tree.updateLock.writer_context():
		# 	self.doLoad(silent=True)


	def forceReload(self):

		with self.tree.writer_context():
			self.log.warning("Forcing a reload of the tree from the database!")
			self.log.warning("Dropping Tree")
			self.tree.dropTree()

			# Flush the dropped tree out of memory
			collected = gc.collect()
			self.log.info("GC collected %s items.", collected)

			self.log.warning("Tree Dropped. Rebuilding")
			self.unlocked_doLoad(silent=False)
			self.log.warning("Tree Rebuilt")

	def unlocked_doLoad(self, silent=False):
		print("DoLoad: ", self.tree, self.tree.nodes, self.tree.root)
		assert self.tree.root is not None
		if self.tree.nodes > 0:
			if not silent:
				self.log.error("Tree already built (%s nodes). Reloading will have no effect!", self.tree.nodes)
				raise ValueError
			return

		cur = self.getStreamingCursor(wantCols=['dbId', 'pHash'], where=(self.table.phash != None))
		loaded = 0

		rows = cur.fetchmany(self.streamChunkSize)
		while rows:
			for dbId, pHash in rows:
				if pHash != None:
					self.tree.unlocked_insert(pHash, dbId)
			loaded += len(rows)
			self.log.info("Loaded %s phash data sets.", loaded)
			rows = cur.fetchmany(self.streamChunkSize)

		cur.close()

	def insertIntoDb(self, *args, **kwargs):
		super().insertIntoDb(*args, **kwargs)

		if 'commit' in kwargs:
			kwargs.pop("commit")

		dbId, itemHash = self.getItem(wantCols=['dbId', 'pHash'], **kwargs)

		# "0" is a valid hash value, so we have to explicitly check for none,
		# rather then allowing type coercion
		if itemHash != None:
			with self.tree.writer_context():
				self.tree.insert(itemHash, dbId)


	def updateDbEntry(self, *args, **kwargs):
		super().updateDbEntry(*args, **kwargs)

		if 'commit' in kwargs:
			kwargs.pop("commit")

		# reinsert every item that would be changed
		# Probably unnecessary.

		ret = self.getItems(wantCols=['dbId', 'pHash'], **kwargs)

		# "0" is a valid hash value, so we have to explicitly check for none,
		# rather then allowing type coercion

		if any([item for item in ret if item[1] != None]):
			with self.tree.writer_context():
				for dbId, itemHash in [item for item in ret if item[1] != None]:
					self.tree.insert(itemHash, dbId)

	def deleteDbRows(self, *args, **kwargs):

		if kwargs:
			ret = self.getItems(wantCols=['dbId', 'pHash'], **kwargs)

		super().deleteDbRows(*args, **kwargs)

		with self.tree.writer_context():
			# If kwargs is not defined, deleteDbRows will error, so we don't
			# care about the additional error of trying to iterate over
			# the (then undefined) ret, since it won't happen.
			for dbId, itemHash in [item for item in ret if item[1]]:
				try:
					self.tree.remove(itemHash, dbId)
				except KeyError:
					self.log.critical("Failure when deleting node?")
					for line in traceback.format_exc().split("\n"):
						self.log.critical(line)
					self.log.critical("Ignoring error")

	def searchPhashSet(self, phash_list, distance):
		ret = {}
		with self.tree.reader_context():
			for phash in phash_list:
				ret[phash] = self.tree.getWithinDistance(phash, distance)

		return ret

	def getRandomPhashRows(self, sample_ratio=0.0005):
		with self.transaction() as cur:
			cur.execute("SELECT dbid, phash FROM {table} TABLESAMPLE SYSTEM(%s);".format(table=self.tableName), (sample_ratio, ))
			ret = cur.fetchall()
			ret = set([tmp for tmp in ret if tmp[1]])
			return ret

	def getWithinDistance_db(self, inPhash, distance=2):
		with self.transaction() as cur:

			cur.execute("SELECT dbid FROM {table} WHERE phash <@ (%s, %s);".format(table=self.tableName), (inPhash, distance))
			ret = cur.fetchall()
			ret = set([tmp[0] for tmp in ret])

			self.log.info("Search for '%s', distance '%s'. Discovered %s match(es)" % (inPhash, distance, len(ret)))

			return ret

	def getIdsWithinDistance(self, inPhash, distance=2):
		with self.tree.reader_context():
			ids = self.tree.getWithinDistance(inPhash, distance)
		return set(ids)

	def getWithinDistance(self, inPhash, distance=2, wantCols=None):
		ids = self.getIdsWithinDistance(inPhash, distance)
		ret = []
		for itemId in ids:
			itemRow = self.getItem(dbId=itemId, wantCols=wantCols)
			# Sometimes a row has been deleted without being removed from the tree.
			# If this has happened, getItem() will return an empty list.
			# Don't return that, if it happens
			if not itemRow:
				self.log.info("Row deleted without updating tree")
			else:
				ret.append(itemRow)

		return ret

