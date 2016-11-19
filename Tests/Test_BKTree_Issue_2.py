
# from cbktree import BkHammingTree, explicitSignCast


import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb

int_bits = lambda b: hamDb.explicitSignCast(int(b, 2))

TEST_DATA = {
	# Format: id -> bitstring
	1: int_bits('1011010010010110110111111000001000001000100011110001010110111011'),
	2: int_bits('1011010010010110110111111000001000000001100011110001010110111011'),
	3: int_bits('1101011110100100001011001101001110010011100010011101001000110101'),
}

SEARCH_DIST = 2  # 2 out of 64 bits




import unittest
import scanner.logSetup as logSetup
from bitstring import Bits

import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb

def hamming(a, b):

	tot = 0

	x = (a ^ b)
	while x > 0:
		tot += x & 1
		x >>= 1
	return tot


def b2i(binaryStringIn):
	if len(binaryStringIn) != 64:
		print("ERROR: Passed string not 64 characters. String length = %s" % len(binaryStringIn))
		print("ERROR: String value '%s'" % binaryStringIn)
		raise ValueError("Input strings must be 64 chars long!")

	val = Bits(bin=binaryStringIn)
	return val.int


class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):
		self.tree = hamDb.BkHammingTree()

		for nodeId, nodeHash in TEST_DATA.items():
			self.tree.insert(nodeHash, nodeId)


	def test_2(self):


		# Find near matches for each node that was inserted.
		for node_id, ib in TEST_DATA.items():
			res = self.tree.getWithinDistance(ib, SEARCH_DIST)
			print("{}: {}".format(node_id, res))

		# Find near matches for items that were not inserted.

		new = '1101011110100100001011001101001110010011100010011101001000110101'
		self.assertEqual(self.tree.getWithinDistance(int_bits(new), SEARCH_DIST), {3})
		print("new: {}".format(self.tree.getWithinDistance(int_bits(new), SEARCH_DIST)))

		ones = '1' * 64
		print("111..: {}".format(self.tree.getWithinDistance(int_bits(ones), SEARCH_DIST)))

		# XXX Should return empty, returns [0] instead.
		zeroes = '0' * 64
		print("000..: {}".format(self.tree.getWithinDistance(int_bits(zeroes), SEARCH_DIST)))


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
