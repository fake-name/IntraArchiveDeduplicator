
import unittest
import scanner.logSetup as logSetup

import os.path

import Tests.basePhashTestSetup


import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb



from Tests.baseArchiveTestSetup import CONTENTS


def fix_paths(tuplelist):
	# Patch in current script directory so the CONTENTS paths work.
	curdir = os.path.dirname(os.path.realpath(__file__))

	tuplelist = [list(item) for item in tuplelist]
	for x in range(len(tuplelist)):
		tuplelist[x][1] = tuplelist[x][1].format(cwd=curdir)
		tuplelist[x] = tuple(tuplelist[x])
	return tuplelist


class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):

		self.addCleanup(self.dropDatabase)

		self.db = Tests.basePhashTestSetup.TestDb()

		# Check the table is set up
		self.assertEqual(self.db.getItemNum(), (len(CONTENTS), ),
				'Setup resulted in an incorrect number of items in database!')

	def dropDatabase(self):
		self.db.tearDown()
		self.db.close()

	def test_treeExists(self):
		self.assertIsInstance(self.db.tree, hamDb.BkHammingTree)


	def test_loadFromDb(self):
		self.db.tree.dropTree()
		self.db.unlocked_doLoad()


	# Verify the structure of the tree
	# does not change across reloading.
	def test_testLoadingDeterminsm(self):
		loadedTree = list(self.db.tree)

		self.db.tree.dropTree()

		self.db.unlocked_doLoad()

		self.assertEqual(list(self.db.tree), loadedTree)


	def test_getDbLoadedProperly(self):

		expect = list(CONTENTS)
		expect.sort()
		items = list(self.db.getItems())
		items.sort()

		self.assertEqual(items, expect)


	def test_searchByPhash1(self):

		expect = {
			(2,  '{cwd}/test_ptree/allArch.zip',          'Lolcat_this_is_mah_job.jpg',       'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429, None, 493, 389),
			(3,  '{cwd}/test_ptree/allArch.zip',          'Lolcat_this_is_mah_job.png',       '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389),
			(4,  '{cwd}/test_ptree/allArch.zip',          'Lolcat_this_is_mah_job_small.jpg', '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237),
			(9,  '{cwd}/test_ptree/notQuiteAllArch.zip',  'Lolcat_this_is_mah_job.jpg',       'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429, None, 493, 389),
			(10, '{cwd}/test_ptree/notQuiteAllArch.zip',  'Lolcat_this_is_mah_job.png',       '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389),
			(11, '{cwd}/test_ptree/notQuiteAllArch.zip',  'Lolcat_this_is_mah_job_small.jpg', '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237),
			(43, '{cwd}/test_ptree/testArch.zip',         'Lolcat_this_is_mah_job_small.jpg', '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237),
			(42, '{cwd}/test_ptree/testArch.zip',         'Lolcat_this_is_mah_job.png',       '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389),

		}

		expect = fix_paths(expect)

		expect = set(expect)

		# Distance of 0 from results
		ret = self.db.getWithinDistance(27427800275512429)
		ret = set(ret)

		self.assertEqual(ret, expect)

		# Distance of 1 from results
		ret = self.db.getWithinDistance(27427800275512428)
		ret = set(ret)
		self.assertEqual(ret, expect)

		# Distance of 2 from results
		ret = self.db.getWithinDistance(27427800275512424)
		ret = set(ret)
		self.assertEqual(ret, expect)


	def test_searchByPhash2(self):
		ret = self.db.getWithinDistance(27427800275512426)
		self.assertEqual(ret, [])

		ret = self.db.getWithinDistance(507)
		self.assertEqual(ret, [])

		ret = self.db.getWithinDistance(-5569898607211671251)
		self.assertEqual(ret, [])


	def test_searchByPhash3(self):


		expect = [
			[6,  '{cwd}/test_ptree/allArch.zip',         'lolcat-crocs.jpg',                 '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
			[12, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-crocs.jpg',                 '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
		]

		expect = fix_paths(expect)

		# Distance of 2 from results
		ret = self.db.getWithinDistance(-5569898607211671279)

		expect = set(expect)
		ret = set(ret)

		print("Expect: ", expect)
		print("ret: ", ret)

		self.assertEqual(ret, expect)



