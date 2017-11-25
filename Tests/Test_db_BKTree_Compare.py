
import unittest
import time
import pprint
import logging
import scanner.logSetup as logSetup

import pyximport
print("Have Cython")
pyximport.install()

import dbPhashApi




class TestCompareDatabaseInterface(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		# We set up and tear down the tree a few times to validate the dropTree function
		self.log = logging.getLogger("Main.TestCompareDatabaseInterface")

		self.tree = dbPhashApi.PhashDbApi()
		self.tree.forceReload()

	def dist_check(self, distance, dbid, phash):

		qtime1 = time.time()
		have1 = self.tree.getWithinDistance_db(phash, distance=distance)
		qtime2 = time.time()
		qtime3 = time.time()
		have2 = self.tree.getIdsWithinDistance(phash, distance=distance)
		qtime4 = time.time()


		# print(dbid, have1)
		if have1 != have2:
			self.log.error("Mismatch!")
			for line in pprint.pformat(have1).split("\n"):
				self.log.error(line)
			for line in pprint.pformat(have2).split("\n"):
				self.log.error(line)

		self.assertTrue(dbid in have1)
		self.assertTrue(dbid in have2)
		self.assertEqual(have1, have2)

		self.log.info('Dist %s %s, %s', distance, qtime2-qtime1, qtime4-qtime3)


	def test_0(self):
		rand_r = self.tree.getRandomPhashRows(0.001)
		self.log.info("Have %s items to test with", len(rand_r))

		stepno = 0
		for dbid, phash in rand_r:
			self.dist_check(1, dbid, phash)
			self.dist_check(2, dbid, phash)
			self.dist_check(3, dbid, phash)
			self.dist_check(4, dbid, phash)
			self.dist_check(5, dbid, phash)
			self.dist_check(6, dbid, phash)
			self.dist_check(7, dbid, phash)
			self.dist_check(8, dbid, phash)
			stepno += 1
			self.log.info("On step %s of %s", stepno, len(rand_r))
