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

def hash_print(phash):

	bits = [1 if 1 << x & phash else 0 for x in range(63, -1, -1)]
	for x in range(0, 64, 8):
		print(bits[x:x+8])


def hash_comp(phash1, phash2):

	bits1 = [1 if 1 << x & phash1 else 0 for x in range(63, -1, -1)]
	bits2 = [1 if 1 << x & phash2 else 0 for x in range(63, -1, -1)]
	distance = len([1 for b in range(64) if bits1[b] != bits2[b]])
	print("Distance: ", distance)
	for x in range(0, 64, 8):
		diff = [[1 if bits1[b] != bits2[b] else 0 for b in range(7+x, -1+x, -1)]]
		print(bits1[x:x+8], bits2[x:x+8], diff)


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
	print(commons)
	print("Wut?")

def doSingleSearch(phash):
	print("Search for: ", phash)
	phash = int(phash)
	hash_print(phash)
	print(phash)

	print("Finding files similar to: '{}'".format(phash))
	remote = rpyc.connect("localhost", 12345)
	commons = remote.root.single_phash_search(phash=phash)

	print("Common files:")
	for item in commons:
		print(item[1].ljust(100), item[0])
		hash_comp(phash, item[4])

def go(scanConf):
	if scanConf.testScan:
		doTestScan(scanConf.testScan)
	elif scanConf.listSimilar:
		doListDupes(scanConf.listSimilar)
	elif scanConf.phashLookup:
		doSingleSearch(scanConf.phashLookup)


