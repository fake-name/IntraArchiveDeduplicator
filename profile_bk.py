
import unittest
import cProfile
import scanner.logSetup as logSetup

import random

import pyximport
print("Have Cython")
pyximport.install()



import deduplicator.cyHamDb as hamDb

TREE_ENTRIES = 1000000
# TREE_ENTRIES = 10000
TEST_QUERIES = 1000

SEARCH_DIST = 4

class ProfileTree():

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.buildTestTree()

	def buildTestTree(self):
		self.tree = hamDb.BkHammingTree()

		# Fix the random ordering so profile results
		# are sensible
		random.seed(65413654911)

		print("Building test-tree with %s nodes" % TREE_ENTRIES)
		for x in range(TREE_ENTRIES):
			fk_hash = random.getrandbits(64)
			fk_hash = hamDb.explicitSignCast(fk_hash)
			self.tree.insert(fk_hash, x)
			if x % 10000 == 0:
				print("Inserted %s items, %s%% complete" % (x, (x / TREE_ENTRIES * 100)))
		print("Tree built")

	def do_test_queries(self):
		print("Doing test queries")
		for x in range(TEST_QUERIES):
			fk_hash = random.getrandbits(64)
			fk_hash = hamDb.explicitSignCast(fk_hash)
			self.tree.getWithinDistance(fk_hash, SEARCH_DIST)
		print("Test queries complete")


def test_cpp():
	item = hamDb.CppBkHammingTree()
	print(item)
	del item
	print("Complete")

if __name__ == '__main__':
	import sys
	if "prof" in sys.argv:
		prof = ProfileTree()
		prof.buildTestTree()
		cProfile.run('prof.do_test_queries()', "query_stats.cprof")
	elif "cpp" in sys.argv:
		test_cpp()
	elif "anal" in sys.argv:
		import pstats
		p = pstats.Stats("query_stats.cprof")
		p.strip_dirs().sort_stats(-1).print_stats()

		p.sort_stats('cumulative').print_stats()
		p.sort_stats('time').print_stats()
	else:
		print("Supported args:")
		print('	"prof"')
		print('	"cpp"')
		print('	"anal"')