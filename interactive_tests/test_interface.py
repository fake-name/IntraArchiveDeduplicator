#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import rpyc
import os.path
import sys
import scanner.logSetup

import multiprocessing
import scanner.runState

import logging
import pprint

import random
random.seed()

import signal
import scanner.uiFrontend
import scanner.hashFile as hasher
import UniversalArchiveInterface as uar

def rawHashFile(archPath):
	archIterator = uar.ArchiveReader(archPath)

	fnames = [item[0] for item in archIterator]
	fset = set(fnames)
	if len(fnames) != len(fset):
		print(fnames)
		print(fset)
		raise ValueError("Wat?")

	try:
		for fName, fp in archIterator:
			fCont = fp.read()
			fName, hexHash, pHash, imX, imY = hasher.hashFile(archPath, fName, fCont)

			insertArgs = {
						"internalPath" :fName.rjust(25),
						"itemHash"     :hexHash,
						"pHash"        :str(pHash).rjust(25),
					}

			print(insertArgs)
	except:
		print(archPath)
		raise


def doTestScan(on_file):
	print("Doing a test-scan on file: '{}'".format(on_file))
	rawHashFile(on_file)


def doListDupes(on_file):
	print("Finding files similar to: '{}'".format(on_file))
	remote = rpyc.connect("localhost", 12345)
	commons = remote.root.listDupes(filePath=on_file)
	print("result:")
	pprint.pprint(commons)
	print("Wut?")

def doSingleSearch(phash):
	print("Search for: ", phash)
	phash = int(phash)
	print(phash)

	print("Finding files similar to: '{}'".format(phash))
	remote = rpyc.connect("localhost", 12345)
	commons = remote.root.single_phash_search(phash=phash)

	print("Common:")
	print(commons)

def go(scanConf):
	if scanConf.testScan:
		doTestScan(scanConf.testScan)
	elif scanConf.listSimilar:
		doListDupes(scanConf.listSimilar)
	elif scanConf.phashLookup:
		doSingleSearch(scanConf.phashLookup)


