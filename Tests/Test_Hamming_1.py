
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


	def test_distance_old(self):

		v1 = b2i("0000000000000000000000000000000000000000000000000000000000000000")
		v2 = b2i("1111111111111111111111111111111111111111111111111111111111111111")
		v3 = b2i("0000000000000000000000000000000000000001111111111111111000000000")
		v4 = b2i("1000000000000000000000000000000000000000000000000000000000000000")
		v5 = b2i("0000000000000000000000000000000000000000000000000000000000000001")
		v6 = b2i("1100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(hamDb.hamming_dist(v1, v2), 64)
		self.assertEqual(hamDb.hamming_dist(v3, v2), 48)

		self.assertEqual(hamDb.hamming_dist(v2, v4), 63)
		self.assertEqual(hamDb.hamming_dist(v2, v5), 63)

		self.assertEqual(hamDb.hamming_dist(v1, v4), 1)
		self.assertEqual(hamDb.hamming_dist(v1, v5), 1)
		self.assertEqual(hamDb.hamming_dist(v1, v6), 2)



	def test_distance_new(self):

		v1 = b2i("0000000000000000000000000000000000000000000000000000000000000000")
		v2 = b2i("1111111111111111111111111111111111111111111111111111111111111111")
		v3 = b2i("0000000000000000000000000000000000000001111111111111111000000000")
		v4 = b2i("1000000000000000000000000000000000000000000000000000000000000000")
		v5 = b2i("0000000000000000000000000000000000000000000000000000000000000001")
		v6 = b2i("1100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(hamDb.f_hamming_dist(v1, v2), 64)
		self.assertEqual(hamDb.f_hamming_dist(v3, v2), 48)

		self.assertEqual(hamDb.f_hamming_dist(v2, v4), 63)
		self.assertEqual(hamDb.f_hamming_dist(v2, v5), 63)

		self.assertEqual(hamDb.f_hamming_dist(v1, v4), 1)
		self.assertEqual(hamDb.f_hamming_dist(v1, v5), 1)
		self.assertEqual(hamDb.f_hamming_dist(v1, v6), 2)


