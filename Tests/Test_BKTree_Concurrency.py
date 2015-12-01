
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

TREE_SIZE = 8 * 1000 * 1000
TEST_SAMPLE_SIZE = 1*1000

def lookup_call(tree, nlookups, offset):
	local_random = random.Random()
	local_random.seed(RANDOM_INIT)

	# offset = (TREE_SIZE // 2) - TEST_SAMPLE_SIZE
	# Step the random number generator to the end of the search space
	for dummy_x in range(offset):
		local_random.getrandbits(64)

	for nodeId in range(nlookups):
		nodeId += offset
		node_hash = local_random.getrandbits(64) - 2**63
		ret0 = tree.getWithinDistance(node_hash, 0)
		ret1 = tree.getWithinDistance(node_hash, 1)
		ret2 = tree.getWithinDistance(node_hash, 2)
		ret3 = tree.getWithinDistance(node_hash, 3)
		assert ret0 == set((nodeId, ))
		assert ret1 == set((nodeId, ))
		assert ret2 == set((nodeId, ))
		assert ret3 == set((nodeId, ))

def destroy_call(tree, nlookups, offset=0):
	local_random = random.Random()
	local_random.seed(RANDOM_INIT)

	for dummy_x in range(offset):
		local_random.getrandbits(64)

	for nodeId in range(nlookups):
		nodeId += offset
		node_hash = local_random.getrandbits(64) - 2**63
		deleted, removed = tree.remove(node_hash, nodeId)
		assert deleted == 1


class TestSequenceFunctions_FlatTree(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):

		self.tree = hamDb.BkHammingTree()
		print("Building tree")
		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(TREE_SIZE):
			node_hash = local_random.getrandbits(64) - 2**63
			self.tree.insert(node_hash, nodeId)

		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(TREE_SIZE):
			node_hash = local_random.getrandbits(64) - 2**63
			if nodeId % 7 == 0:
				self.tree.insert(node_hash, nodeId)

		print("Built")

		# for nodeId, node_hash in enumerate(TEST_DATA_FLAT):
	def test_single_thread(self, lookup_count=TEST_SAMPLE_SIZE//2):
		lookup_call(tree=self.tree, nlookups=lookup_count, offset=0)


	def test_concurrent_reads(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS):
				executor.submit(lookup_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE)

	def test_read_and_write(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS-3):
				executor.submit(lookup_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=(TREE_SIZE - (TEST_SAMPLE_SIZE * x)))
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE+TEST_SAMPLE_SIZE)

	# Requires `BkHammingTree` instance to be pickleable to work.
	# As such, it does not work.
	# def fails_test_3(self):
	#   with ProcessPoolExecutor(max_workers=THREADS) as executor:
	#       for x in range(THREADS):
	#           executor.submit(proc_call, tree=self.tree, nlookups=10*1000)

