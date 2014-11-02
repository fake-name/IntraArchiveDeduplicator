#!/usr/bin/python
# -*- coding: utf-8 -*-

import dbApi

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb


class PhashDbApi(dbApi.DbApi):


	def __init__(self):
		super().__init__()
		self.tree = hamDb.BkHammingTree()

	def insertIntoDb(self, *args, **kwargs):
		super().insertIntoDb(*args, **kwargs)

		if 'commit' in kwargs:
			kwargs.pop("commit")

		dbId, itemHash = self.getItem(wantCols=['dbId', 'pHash'], **kwargs)

		if itemHash:
			self.tree.insert(itemHash, dbId)



	def updateDbEntry(self, *args, **kwargs):
		super().updateDbEntry(*args, **kwargs)

		if 'commit' in kwargs:
			kwargs.pop("commit")

		# reinsert every item that would be changed
		# Probably unnecessary.
		ret = self.getItems(wantCols=['dbId', 'pHash'], **kwargs)
		for dbId, itemHash in [item for item in ret if item[1]]:
			self.tree.insert(itemHash, dbId)

	def deleteDbRows(self, *args, **kwargs):

		if kwargs:
			ret = self.getItems(wantCols=['dbId', 'pHash'], **kwargs)

		super().deleteDbRows(*args, **kwargs)

		# If kwargs is not defined, deleteDbRows will error, so we don't
		# care about the additional error of trying to iterate over
		# the (then undefined) ret, since it won't happen.
		for dbId, itemHash in [item for item in ret if item[1]]:
			self.tree.remove(itemHash, dbId)


	def getWithinDistance(self, inPhash, distance=2, wantCols=None):
		ids = self.tree.getWithinDistance(inPhash, distance)
		ret = []
		for itemId in ids:
			ret.append(self.getItem(dbId=itemId, wantCols=wantCols))
		return ret

