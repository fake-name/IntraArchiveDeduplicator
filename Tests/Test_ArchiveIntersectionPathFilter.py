
import unittest
import scanner.logSetup as logSetup

import deduplicator.ProcessArchive

import Tests.basePhashTestSetup

import os.path
import scanner.fileHasher

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb

from Tests.baseArchiveTestSetup import CONTENTS

class TestHasher(scanner.fileHasher.HashThread):

	def getDbConnection(self):
		return Tests.basePhashTestSetup.TestDbBare()

# Override the db connection object in the ArchChecker so it uses the testing database.
class TestArchiveChecker(deduplicator.ProcessArchive.ArchChecker):
	hasher = TestHasher
	def getDbConnection(self):
		return Tests.basePhashTestSetup.TestDbBare()

class TestArchChecker(unittest.TestCase):
	maxDiff = None

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)
		self.maxDiff = None


	def setUp(self):

		self.addCleanup(self.dropDatabase)


		self.db = Tests.basePhashTestSetup.TestDb()

		# Check the table is set up
		self.verifyDatabaseLoaded()


	def dropDatabase(self):
		self.db.tree.dropTree()
		self.db.tearDown()
		self.db.close()

	def _reprDatabase(self, db):
		'''
		This prints a reproduction of the db contents that can be pasted right into
		a python file. This makes updating the db template (baseArchiveTestSetup) much
		easier when new files are added to the test-suite.
		'''
		for row in db:
			print('%s, ' % list(row))

	def verifyDatabaseLoaded(self):
		expect = list(CONTENTS)
		expect.sort()
		items = list(self.db.getItems())
		items.sort()
		if items != expect:
			self._reprDatabase(items)

		self.assertEqual(items, expect)

	######################################################################################################################################
	######################################################################################################################################
	# Tests
	######################################################################################################################################
	######################################################################################################################################


	def test_significantlySimilar_1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		ret = ck.getSignificantlySimilarArches(searchDistance=2)
		expect = {
			5:
				[
					'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
				]
		}
		self.assertEqual(ret, expect)
		del ck


	def test_pathNegativeFiltering_nofilter(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		expect = {
			5:
				[
					'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
				]
		}

		ck0 = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		ret0 = ck0.getSignificantlySimilarArches(searchDistance=2)
		print("ck0: ", ck0)
		print("ret0: ", ret0)
		self.assertEqual(ret0, expect)
		del ck0


	def test_pathNegativeFiltering_2(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		# These paths should filter all matches.
		pf1 = ['{cwd}/test_ptree/'.format(cwd=cwd)]

		ck1 = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd), pathNegativeFilter=pf1)
		ret1 = ck1.getSignificantlySimilarArches(searchDistance=2)
		print("ck1: ", ck1)
		print("ret1: ", ret1)
		self.assertEqual(ret1, {})
		del ck1


	def test_pathNegativeFiltering_3(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		# These paths should filter all matches.
		pf2 = ['{cwd}/test'.format(cwd=cwd)]

		ck2 = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd), pathNegativeFilter=pf2)
		ret2 = ck2.getSignificantlySimilarArches(searchDistance=2)
		print("ck2: ", ck2)
		print("ret2: ", ret2)
		self.assertEqual(ret2, {})
		del ck2


	def test_pathNegativeFiltering_4(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		expect = {
			5:
				[
					'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
				]
		}

		# This path should filter no matches.
		pf3 = ['{cwd}/testzzzzzzzzzz'.format(cwd=cwd)]


		ck3 = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd), pathNegativeFilter=pf3)
		ret3 = ck3.getSignificantlySimilarArches(searchDistance=2)
		print("ck3: ", ck3)
		print("ret3: ", ret3)
		self.assertEqual(ret3, expect)
		del ck3


	def test_pathNegativeFiltering_5(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		expect = {
			5:
				[
					'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
				]
		}


		# And this should filter a irrelevant file.
		pf4 = ['{cwd}/test_ptree/regular-u'.format(cwd=cwd)]

		ck4 = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd), pathNegativeFilter=pf4)
		ret4 = ck4.getSignificantlySimilarArches(searchDistance=2)
		print("ck4: ", ck4)
		print("ret4: ", ret4)
		self.assertEqual(ret4, expect)
		del ck4




	# def test_significantlySimilar_3(self):
	# 	cwd = os.path.dirname(os.path.realpath(__file__))
	# 	# Check that we are properly matching larger images
	# 	ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
	# 	ret = ck.getSignificantlySimilarArches(searchDistance=2)

	# 	expect = {
	# 		4:
	# 			[
	# 				'{cwd}/test_ptree/regular.zip'.format(cwd=cwd),
	# 				'{cwd}/test_ptree/small_and_regular.zip'.format(cwd=cwd),
	# 			],
	# 		5:
	# 			[
	# 				'{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd),
	# 			]
	# 	}
	# 	print(expect)
	# 	print(ret)
	# 	self.assertEqual(ret, expect)