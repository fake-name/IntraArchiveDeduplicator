
import unittest
import logSetup
from bitstring import Bits

import numpy as np
import random
random.seed()

import hashFile
import unitConverters


def b2i(binaryStringIn):
	if len(binaryStringIn) != 64:
		raise ValueError("Input strings must be 64 chars long!")

	val = Bits(bin=binaryStringIn)
	return val.int





TEST_ARRS = [
	(
		[[ True,  True,  True, False, False,  True,  True,  True],
		 [ True, False, False, False, False,  True,  True,  True],
		 [ True, False, False,  True, False, False,  True, False],
		 [False, False,  True, False,  True,  True, False,  True],
		 [ True,  True, False, False,  True, False, False,  True],
		 [False, False, False, False,  True,  True, False,  True],
		 [False,  True, False,  True, False, False, False,  True],
		 [ True, False,  True, False, False,  True,  True,  True]],
		"1110011110000111100100100010110111001001000011010101000110100111"
	),

	(
		[[False,  True, False, False, False, False, False, False],
		 [False,  True,  True, False, False,  True, False,  True],
		 [ True,  True,  True,  True,  True,  True,  True, False],
		 [False,  True, False,  True, False,  True,  True,  True],
		 [False,  True,  True,  True, False,  True,  True,  True],
		 [ True, False,  True,  True,  True, False,  True, False],
		 [ True,  True, False, False, False,  True, False,  True],
		 [ True,  True,  True,  True,  True, False,  True,  True]],
		"0100000001100101111111100101011101110111101110101100010111111011"
	),

	(
		[[ True, False,  True, False,  True, False,  True,  True],
		 [False,  True,  True, False, False, False,  True, False],
		 [ True, False,  True,  True,  True, False, False, False],
		 [ True, False,  True, False,  True,  True, False, False],
		 [False, False, False,  True, False,  True, False, False],
		 [False, False,  True,  True, False, False,  True,  True],
		 [ True,  True,  True,  True,  True, False, False,  True],
		 [False,  True,  True,  True,  True, False, False, False]],
		"1010101101100010101110001010110000010100001100111111100101111000"
	),

	(
		[[ True,  True, False,  True,  True,  True, False, False],
		 [ True,  True, False, False,  True,  True, False, False],
		 [False, False,  True, False,  True,  True, False,  True],
		 [ True, False,  True,  True, False,  True, False, False],
		 [ True, False,  True, False,  True, False, False,  True],
		 [ True, False, False,  True,  True,  True, False,  True],
		 [False, False, False, False, False, False, False,  True],
		 [ True,  True,  True, False, False,  True,  True,  True]],
		"1101110011001100001011011011010010101001100111010000000111100111"
	),

	(
		[[False,  True,  True, False, False, False, False,  True],
		 [False,  True, False,  True, False, False, False,  True],
		 [ True, False, False, False, False,  True,  True,  True],
		 [ True,  True, False, False, False,  True, False, False],
		 [False,  True, False,  True,  True, False, False, False],
		 [ True,  True,  True,  True, False,  True, False, False],
		 [ True, False, False,  True,  True, False,  True,  True],
		 [ True,  True, False,  True,  True,  True,  True, False]],
		"0110000101010001100001111100010001011000111101001001101111011110"
	)

]





class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def test_binConversions(self):
		val = b2i("0000000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, 0)
		val = b2i("1111111111111111111111111111111111111111111111111111111111111111")
		self.assertEqual(val, -1)
		val = b2i("1000000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, -9223372036854775808)
		val = b2i("0111111111111111111111111111111111111111111111111111111111111111")
		self.assertEqual(val, 9223372036854775807)
		val = b2i("1100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, -4611686018427387904)
		val = b2i("0100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, 4611686018427387904)
		self.assertRaises(ValueError, b2i, "101")

	def test_binConversions2(self):
		val = unitConverters.binStrToInt("0000000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, 0)
		val = unitConverters.binStrToInt("1111111111111111111111111111111111111111111111111111111111111111")
		self.assertEqual(val, -1)
		val = unitConverters.binStrToInt("1000000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, -9223372036854775808)
		val = unitConverters.binStrToInt("0111111111111111111111111111111111111111111111111111111111111111")
		self.assertEqual(val, 9223372036854775807)
		val = unitConverters.binStrToInt("1100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, -4611686018427387904)
		val = unitConverters.binStrToInt("0100000000000000000000000000000000000000000000000000000000000000")
		self.assertEqual(val, 4611686018427387904)
		self.assertRaises(ValueError, b2i, "101")

	def test_binConversions3(self):
		# Kinda brute-forcey random testing, but it'll work for the moment.
		for x in range(1000):
			test = ''.join([str(random.randrange(0, 2, 1)) for x in range(64)])
			self.assertEqual(b2i(test), unitConverters.binStrToInt(test))


	def test_numpyConversions(self):
		for arr, valStr in TEST_ARRS:
			arr = np.array(arr)

			st = "".join(["1" if dat else '0' for dat in arr.flatten() ])
			val = b2i(valStr)
			self.assertEqual(unitConverters.binary_array_to_int(arr), val)
			self.assertEqual(b2i(st), val)
			self.assertEqual(valStr, st)

