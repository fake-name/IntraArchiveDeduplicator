
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

THREADS = 12
RANDOM_INIT = 6461351

TEST_SAMPLE_SIZE = 1 * 1000

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

def insert_call(tree, nlookups, offset=0, hash_offset=0):
	local_random = random.Random()
	local_random.seed(RANDOM_INIT)

	for dummy_x in range(offset):
		local_random.getrandbits(64)

	for nodeId in range(nlookups):
		node_hash = (local_random.getrandbits(64) - 2**63)+hash_offset
		tree.insert(node_hash, nodeId)

import os


def _VmB(VmKey):
	_proc_status = '/proc/%d/status' % os.getpid()
	 # get pseudo file  /proc/<pid>/status
	try:
		t = open(_proc_status)
		v = t.read()
		t.close()
	except:
		return 0.0  # non-Linux?
	 # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
	i = v.index(VmKey)
	v = v[i:].split(None, 3)  # whitespace
	if len(v) < 3:
		return 0.0  # invalid format?
	 # convert Vm value to bytes
	return float(v[1])


def memory(since=0.0):
	'''Return memory usage in bytes.
	'''
	return _VmB('VmSize:') - since


def resident(since=0.0):
	'''Return resident memory usage in bytes.
	'''
	return _VmB('VmRSS:') - since


class TestTreeLeaks(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		self.tree_size = 100 * 1000
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.tree = hamDb.BkHammingTree()
		print("Warming memory")
		for x in range(3):
			self.buildTestTree()

	def buildTestTree(self):

		with self.tree.writer_context():
			self.tree.dropTree()
			print("Building test tree with size: %s" % self.tree_size)
			local_random = random.Random()
			for nodeId in range(self.tree_size):
				node_hash = local_random.getrandbits(64) - 2**63
				self.tree.unlocked_insert(node_hash, nodeId)



		# for nodeId, node_hash in enumerate(TEST_DATA_FLAT):
	def test_single_thread(self):
		base_mem = resident()
		used = []
		for x in range(50):
			self.buildTestTree()
			used.append(resident(base_mem))
			print("Used memory:", used[-1])

		print("Memory change:", used)
		# Used values is apparently reported in pages, so
		# 1000 == ~4MBytes
		assert max(used) < 1000

class TestSequenceFunctions_ConcurrentModification(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		self.tree_size = 100 * 1000
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):

		self.tree = hamDb.BkHammingTree()
		print("Building test tree with size: %s" % self.tree_size)
		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(self.tree_size):
			node_hash = local_random.getrandbits(64) - 2**63
			self.tree.insert(node_hash, nodeId)

		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(self.tree_size):
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

	def test_read_and_delete(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS-3):
				executor.submit(lookup_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=(self.tree_size - (TEST_SAMPLE_SIZE * x)))
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE+TEST_SAMPLE_SIZE)


	def test_read_and_write(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS-3):
				executor.submit(lookup_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=(self.tree_size - (TEST_SAMPLE_SIZE * x)))
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*0)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*1)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*2)

			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*3)
			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*4)
			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*5)

	def test_read_and_write_2(self):
		with ThreadPoolExecutor(max_workers=THREADS) as executor:
			for x in range(THREADS-3):
				executor.submit(lookup_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=(self.tree_size - (TEST_SAMPLE_SIZE * x)))
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*0)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*1)
			executor.submit(destroy_call, tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*2)

			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*0, hash_offset=10500)
			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*1, hash_offset=10500)
			executor.submit(insert_call,  tree=self.tree, nlookups=TEST_SAMPLE_SIZE, offset=TEST_SAMPLE_SIZE*2, hash_offset=10500)


class TestSequenceFunctions_ConcurrentModificationVerification(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)
		self.tree_size = 100 * 1000

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):

		self.tree = hamDb.BkHammingTree()
		print("Building test tree with size: %s" % self.tree_size)
		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(self.tree_size):
			node_hash = local_random.getrandbits(64) - 2**63
			self.tree.insert(node_hash, nodeId)

		local_random = random.Random()
		local_random.seed(RANDOM_INIT)
		for nodeId in range(self.tree_size):
			node_hash = local_random.getrandbits(64) - 2**63
			if nodeId % 7 == 0:
				self.tree.insert(node_hash, nodeId)

		print("Built")

		# for nodeId, node_hash in enumerate(TEST_DATA_FLAT):
	def test_single_thread(self, lookup_count=TEST_SAMPLE_SIZE//2):
		lookup_call(tree=self.tree, nlookups=lookup_count, offset=0)



	# Requires `BkHammingTree` instance to be pickleable to work.
	# As such, it does not work.
	# def fails_test_3(self):
	#   with ProcessPoolExecutor(max_workers=THREADS) as executor:
	#       for x in range(THREADS):
	#           executor.submit(proc_call, tree=self.tree, nlookups=10*1000)

