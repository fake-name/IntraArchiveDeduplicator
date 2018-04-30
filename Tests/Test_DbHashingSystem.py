
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
		self.maxDiff = None

	def setUp(self):

		self.addCleanup(self.dropDatabase)

		self.db = Tests.basePhashTestSetup.TestDb()

		# Check the table is set up
		self.assertEqual(self.db.getItemNum(), (len(CONTENTS), ),
				'Setup resulted in an incorrect number of items in database!')

	def dropDatabase(self):
		self.db.tearDown()
		self.db.close()


	def test_loadFromDb(self):
		self.db.unlocked_doLoad()


	def test_getDbLoadedProperly(self):

		expect = list(CONTENTS)
		expect.sort()
		items = list(self.db.getItems())
		items.sort()

		self.assertEqual(items, expect)


	def test_searchByPhash1(self):

		expect = {
			2,
			3,
			4,
			9,
			10,
			11,
			50,
			49,

		}

		expect = set(expect)

		# Distance of 0 from results
		ret = self.db.getWithinDistance(-4992890192511777340)
		ret = set(ret)

		self.assertEqual(ret, expect)

		# Distance of 1 from results
		ret = self.db.getWithinDistance(-4992890192511777339)
		ret = set(ret)
		self.assertEqual(ret, expect)

		# Distance of 2 from results
		ret = self.db.getWithinDistance(-4992890192511777337)
		ret = set(ret)
		self.assertEqual(ret, expect)


	def test_searchByPhash2(self):
		ret = self.db.getWithinDistance(27427800275512426)
		self.assertEqual(ret, set())

		ret = self.db.getWithinDistance(507)
		self.assertEqual(ret, set())

		ret = self.db.getWithinDistance(-5569898607211671251)
		self.assertEqual(ret, set())


	def test_searchByPhash3(self):


		expect = [
			6,
			12,
		]

		# Distance of 2 from results
		ret = self.db.getWithinDistance(-7472365462264617431)

		expect = set(expect)
		ret = set(ret)

		print("Expect: ", expect)
		print("ret: ", ret)

		self.assertEqual(ret, expect)



