#!/usr/bin/python
# -*- coding: utf-8 -*-

import dbApi
import runState
import logging
import os.path
import queue
import threading

import sys

class Deduper(object):

	def __init__(self, targetDir):
		self.dbInt = dbApi.DbApi()
		self.target = targetDir


	def go(self, args):
		print("Fetching duplicates on base-path '%s'!" % self.target)
		ret = self.dbInt.getDuplicateImages(self.target)
		print("Number of base archives:", len(ret))
		for basepath in ret:
			if self.target in basepath:


				otherBases = set()
				isDuplicated = True
				for dummy_fsPath, dummy_internalPath, itemhash, phash in self.dbInt.getItemsOnBasePath(basepath):
					otherItems = self.dbInt.getByHash(itemhash)
					if len(otherItems) < 2:
						isDuplicated = False
					else:
						for fsPath, dummy_internalPath, dummy_itemhash in otherItems:
							otherBases.add(fsPath)
				if isDuplicated:
					print("Looks to be completely duplicated", basepath)
					for itemPath in otherBases:

						print("	", itemPath)

	def cleanDupFiles(self, args):
		print("Fetching duplicates on base-path '%s'!" % self.target)
		ret = self.dbInt.getDuplicateBaseFiles(self.target)
		print("Number of base archives:", len(ret))
		for basepath, itemhash in ret:
			print("item", basepath)
			dups = self.dbInt.getByHash(itemhash)
			for dup in dups:
				print("	", dup)

	@classmethod
	def dedupe(cls, args):
		print("Dedupe called", args)

		runner = cls(args.targetDir)
		runner.cleanDupFiles(args)
