
import unittest
import scanner.logSetup as logSetup
from bitstring import Bits
import random
import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor

def hamming(a, b):
	tot = 0
	x = (a ^ b)
	while x > 0:
		tot += x & 1
		x >>= 1
	return tot

THREADS = 8
RANDOM_INIT = 6461351

def proc_test(tree, nlookups):
	local_random = random.Random()
	local_random.seed(RANDOM_INIT)
	for nodeId in range(nlookups):
		node_hash = local_random.getrandbits(64) - 2**63
		ret0 = tree.getWithinDistance(node_hash, 0)
		ret1 = tree.getWithinDistance(node_hash, 1)
		ret2 = tree.getWithinDistance(node_hash, 2)
		ret3 = tree.getWithinDistance(node_hash, 3)
		assert ret0 == set((nodeId, ))
		assert ret1 == set((nodeId, ))
		assert ret2 == set((nodeId, ))
		assert ret3 == set((nodeId, ))


class TestSequenceFunctions_FlatTree(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):
		random.seed(RANDOM_INIT)
		self.tree = hamDb.BkHammingTree()
		print("Building tree")
		for nodeId in range(8 * 1000 * 1000):
			node_hash = random.getrandbits(64) - 2**63
			self.tree.insert(node_hash, nodeId)
		print("Built")

		# for nodeId, node_hash in enumerate(TEST_DATA_FLAT):
	def test_1(self, lookup_count=5000):
		proc_test(tree=self.tree, nlookups=lookup_count)


	def test_2(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS):
				executor.submit(proc_test, tree=self.tree, nlookups=10*1000)

	# Requires `BkHammingTree` instance to be pickleable to work.
	# As such, it does not work.
	def fails_test_3(self):
		with ProcessPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS):
				executor.submit(proc_test, tree=self.tree, nlookups=10*1000)

