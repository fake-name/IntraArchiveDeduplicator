
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

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

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



	def test_isBinaryUnique(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		ret = ck.getSignificantlySimilarArches()
		expect = {
			5:
				[
					'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
				]
		}
		self.assertEqual(ret, expect)


		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		ret = ck.getSignificantlySimilarArches()

		expect = {
			4:
				[
					'{cwd}/test_ptree/small.zip'.format(cwd=cwd)
				]
		}
		self.assertEqual(ret, expect)

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		ret = ck.getSignificantlySimilarArches()

		expect = {
			4:
				[
					'{cwd}/test_ptree/regular.zip'.format(cwd=cwd)
				]
		}
		self.assertEqual(ret, expect)




	def test_junkFileFiltering(self):

		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))


		ret = ck.getSignificantlySimilarArches()

		expect = {
			2:
				[
					'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd),
					'{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd)
				]
		}

		self.assertEqual(ret, expect)

