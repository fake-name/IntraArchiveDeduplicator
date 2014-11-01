
import unittest
import logSetup
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



# Node ID numbers are derived from the list ordering.
TEST_DATA = [
	"0000000000000000000000000000000000000000000000000000000000000000",  # 0
	"1111111111111111111111111111111111111111111111111111111111111111",  # 1
	"1000000000000000000000000000000000000000000000000000000000000000",  # 2
	"0111111111111111111111111111111111111111111111111111111111111111",  # 3
	"1100000000000000000000000000000000000000000000000000000000000000",  # 4
	"0100000000000000000000000000000000000000000000000000000000000000",  # 5
	"0000000000000000000000000000000000000001111111111111111000000000",  # 6
	"0000000000000000000000000000000000000001111111111111111000000000",  # 7
	"0000000000000000000000000000000000000001111111111111111000000000"   # 8
]

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):
		self.tree = hamDb.BkHammingTree()

		for nodeId, nodeHash in enumerate(TEST_DATA):
			nodeHash = b2i(nodeHash)
			self.tree.insert(nodeHash, nodeId)

	def test_1(self):
		tgtHash = "0100000000000000000000000000000000000000000000000000000000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 0)
		self.assertEqual(ret, set((5, )))

	def test_2(self):
		tgtHash = "0100000000000000000000000000000000000000000000000000000000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 1)
		self.assertEqual(ret, set((0, 4, 5)))

	def test_3(self):
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 0)
		self.assertEqual(ret, set((6, 7, 8)))

	def test_4(self):
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 15)
		self.assertEqual(ret, set((6, 7, 8)))

	def test_5(self):
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 16)
		self.assertEqual(ret, set((0, 6, 7, 8)))

	def test_6(self):
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 17)
		self.assertEqual(ret, set((0, 2, 5, 6, 7, 8)))

	def test_7(self):
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 18)
		self.assertEqual(ret, set((0, 2, 4, 5, 6, 7, 8)))

	def test_8(self):
		tgtHash = "1000000000000000000000000000000000000000000000000000000000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 0)
		self.assertEqual(ret, set((2, )))

	def test_remove(self):
		rm = 7
		rmHash = b2i(TEST_DATA[rm])
		self.tree.remove(rmHash, rm)
		tgtHash = "0000000000000000000000000000000000000001111111111111111000000000"
		tgtHash = b2i(tgtHash)
		ret = self.tree.getWithinDistance(tgtHash, 15)
		self.assertEqual(ret, set((6, 8)))

	def test_insert(self):
		key = len(TEST_DATA) + 1

		# tgtHash


	def test_distance(self):

		v1 = b2i("0000000000000000000000000000000000000000000000000000000000000000")
		v2 = b2i("1111111111111111111111111111111111111111111111111111111111111111")
		v3 = b2i("0000000000000000000000000000000000000001111111111111111000000000")
		v4 = b2i("1000000000000000000000000000000000000000000000000000000000000000")
		v5 = b2i("0000000000000000000000000000000000000000000000000000000000000001")
		self.assertEqual(hamDb.hamming_dist(v1, v2), 64)
		self.assertEqual(hamDb.hamming_dist(v3, v2), 48)

		self.assertEqual(hamDb.hamming_dist(v2, v4), 63)
		self.assertEqual(hamDb.hamming_dist(v2, v5), 63)

		self.assertEqual(hamDb.hamming_dist(v1, v4), 1)
		self.assertEqual(hamDb.hamming_dist(v1, v5), 1)


