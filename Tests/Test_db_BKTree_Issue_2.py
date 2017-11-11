
# from cbktree import BkHammingTree, explicitSignCast


import unittest
import logging
import scanner.logSetup as logSetup
from bitstring import Bits

import pyximport
print("Have Cython")
pyximport.install()

import Tests.baseDbBkTree
import deduplicator.cyHamDb as hamDb

int_bits = lambda b: hamDb.explicitSignCast(int(b, 2))

TEST_DATA = {
	# Format: id -> bitstring
	1: int_bits('1011010010010110110111111000001000001000100011110001010110111011'),
	2: int_bits('1011010010010110110111111000001000000001100011110001010110111011'),
	3: int_bits('1101011110100100001011001101001110010011100010011101001000110101'),
}

SEARCH_DIST = 2  # 2 out of 64 bits


class TestBkTreeIssue2(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		self.log = logging.getLogger("Main.TestBkTreeIssue2")

		super().__init__(*args, **kwargs)

	def setUp(self):
		# We set up and tear down the tree a few times to validate the dropTree function
		self.tree = Tests.baseDbBkTree.TestBkPhashDb()
		self.buildTestTree()

	def tearDown(self):
		self.tree.tearDown()

	def buildTestTree(self):
		with self.tree.transaction() as cur:
			for nodeId, node_hash in TEST_DATA.items():
				self.tree.insert(cur=cur, node_hash=node_hash, nodeId=nodeId)

	def test_2(self):


		# Find near matches for each node that was inserted.
		for node_id, ib in TEST_DATA.items():
			res = self.tree.getWithinDistance(ib, SEARCH_DIST)
			# print("{}: {}".format(node_id, res))

		# Find near matches for items that were not inserted.

		new = '1101011110100100001011001101001110010011100010011101001000110101'
		self.assertEqual(self.tree.getWithinDistance(int_bits(new), SEARCH_DIST), {3})
		# print("new: {}".format(self.tree.getWithinDistance(int_bits(new), SEARCH_DIST)))

		ones = '1' * 64
		# print("111..: {}".format(self.tree.getWithinDistance(int_bits(ones), SEARCH_DIST)))

		# XXX Should return empty, returns [0] instead.
		zeroes = '0' * 64
		# print("000..: {}".format(self.tree.getWithinDistance(int_bits(zeroes), SEARCH_DIST)))


		self.assertEqual(self.tree.getWithinDistance(int_bits(ones), SEARCH_DIST), set())
		self.assertEqual(self.tree.getWithinDistance(int_bits(zeroes), SEARCH_DIST), set())


	# def test_1(self):
	# 	tgtHash = -6076574518398440533
	# 	ret = self.tree.getWithinDistance(tgtHash, 2)
	# 	self.assertEqual(ret, set([item[0] for item in TEST_DATA]))


	# def test_signModification_1(self):
	# 	x = hamDb.explicitUnsignCast(5)
	# 	x = hamDb.explicitSignCast(x)
	# 	self.assertEqual(x, 5)

	# 	tgtHash = -6076574518398440533

	# 	for hashVal in [data[1] for data in TEST_DATA]:
	# 		x = hamDb.explicitUnsignCast(hashVal)
	# 		x = hamDb.explicitSignCast(x)

	# 		self.assertEqual(hashVal, x)

	# 		# pr = hamDb.explicitUnsignCast(tgtHash) ^ hamDb.explicitUnsignCast(hashVal)

	# 		# print("{0:b}".format(hamDb.explicitUnsignCast(tgtHash)).zfill(64))
	# 		# print("{0:b}".format(hamDb.explicitUnsignCast(hashVal)).zfill(64))
	# 		# print("{0:b}".format(pr).zfill(64).replace("0", " "))
	# 		# print()
