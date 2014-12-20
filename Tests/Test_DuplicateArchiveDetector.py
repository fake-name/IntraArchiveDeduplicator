
import unittest
import scanner.logSetup as logSetup

import deduplicator.ProcessArchive

import Tests.basePhashTestSetup

import os.path

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb

from Tests.baseArchiveTestSetup import CONTENTS

# Override the db connection object in the ArchChecker so it uses the testing database.
class TestArchiveChecker(deduplicator.ProcessArchive.ArchChecker):
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

	def test_getItemsSimple(self):
		self.verifyDatabaseLoaded()


	def test_isBinaryUnique(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		print(ck.isBinaryUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertTrue(ck.isBinaryUnique())

	def test_isPhashUnique(self):
		cwd = os.path.dirname(os.path.realpath(__file__))


		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertTrue(ck.isPhashUnique())

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertTrue(ck.isPhashUnique())

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.isPhashUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		self.assertFalse(ck.isPhashUnique())


	def test_getBestMatch_1(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/regular.zip'.format(cwd=cwd))


		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))


		# The `notQuiteAllArch` has both binary and phash duplicates (since phash duplicates
		# are a superset of binary duplicates, if you have binary duplicates, you by definition
		# must have phash duplicates.)
		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(),  '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))

	def test_getBestMatch_2(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		# z_reg and z_reg_junk should be commutative, as they contain identical non-filtered files.
		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))


		# z_sml should best-match z_reg_junk, because z_reg_junk is larger on-disk then z_reg
		# This is annoying, but short of opening the archive and taking the size of all the
		# valid contents, I don't really see a better approach.
		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))

		# The fact that getBestBinaryMatch() returns `z_reg_junk` is non-intuitive, but correct.
		# Basically, z_sml /is/ completely duplicated, albeit across multiple archives. The text-file
		# `test.txt` is duplicated in z_reg_junk, and the image is duplicated in `z_sml_u`. Therefore,
		# isUnique() returns false, so getMatchingArchives() returns a set of partially intersecting
		# archives.
		# This set is then sorted by archive size, and since `z_sml_u` is smaller then `z_reg_junk`,
		# `z_reg_junk` is returned.
		# TL;DR z_sml is duplicated by two partial dups that overlap for 100% coverage.
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Remove z_sml_u so we don't match to it for binary matching.
		os.remove('{cwd}/test_ptree/z_sml_u.zip'.format(cwd=cwd))

		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Remove junk zip so z_sml matches to z_reg now.
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))



	def test_getAllMatches(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})
		self.assertEqual(ck.getPhashMatchingArchives(), {})

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})
		self.assertEqual(ck.getPhashMatchingArchives(), {})


		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})

		match = {
			'{cwd}/test_ptree/regular.zip'.format(cwd=cwd):
				{
					'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',
					'funny-pictures-cat-looks-like-an-owl.jpg',
					'funny-pictures-cat-will-do-science.jpg',
					'funny-pictures-kitten-rules-a-tower.jpg'
				}
			}
		self.assertEqual(ck.getPhashMatchingArchives(), match)

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		match = {
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_reg.zip':
			{
				'test.txt'
			},
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_sml_u.zip':
			{
				'129165237051396578(s).jpg'
			}
		}


		pmatch = {
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_reg.zip':
			{
				'129165237051396578.jpg',
				'test.txt'
			},
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_sml_u.zip':
			{
				'129165237051396578(s).jpg'
			}
		}


		self.assertEqual(ck.getMatchingArchives(),      match)
		self.assertEqual(ck.getPhashMatchingArchives(), pmatch)


		# The `notQuiteAllArch` has both binary and phash duplicates (since phash duplicates
		# are a superset of binary duplicates, if you have binary duplicates, you by definition
		# must have phash duplicates.)
		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		match = {
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/testArch.zip':
				{
					'Lolcat_this_is_mah_job.png',
					'Lolcat_this_is_mah_job_small.jpg'
				},
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/allArch.zip':
				{
					'Lolcat_this_is_mah_job.jpg',
					'lolcat-crocs.jpg',
					'Lolcat_this_is_mah_job.png',
					'Lolcat_this_is_mah_job_small.jpg',
					'lolcat-oregon-trail.jpg'
				}
			}
		self.assertEqual(ck.getMatchingArchives(),      match)
		self.assertEqual(ck.getPhashMatchingArchives(), match)

	def test_noMatch(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml_u.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})
		self.assertEqual(ck.getPhashMatchingArchives(), {})

	def test_itemRemoved(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zips so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))
		os.remove('{cwd}/test_ptree/z_sml_u.zip'.format(cwd=cwd))

		# Check archive matches normally.
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/regular.zip'.format(cwd=cwd))

		# Remove the matching arch
		os.remove('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))

		# Verify the match now fails
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())


		# For a different archive.
		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))

		# Remove the matching dir
		os.remove('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())


		# The `notQuiteAllArch` has both binary and phash duplicates (since phash duplicates
		# are a superset of binary duplicates, if you have binary duplicates, you by definition
		# must have phash duplicates.)
		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(),  '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))

		# Remove the matching dir
		os.remove('{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))

		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestPhashMatch())
		self.assertFalse(ck.getBestBinaryMatch())


	def test_skipSolid(self):
		'''
		z_sml_w is a solid-color image, which produces a phash of 0.
		since there are LOTS of empty page images, this is basically a useless match, so it's
		special-case skipped in the ProcessArchive tool. Otherwise, we'd be waiting on
		10K+ file existence checks, which is slow.

		Only the phash-system has this special-case behaviour, so we expect no matches for
		the normal binary match, and lots of matches for the text file.
		'''

		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml_w.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})

		p_expect = {
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_reg.zip':
			{
				'test.txt'
			},
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_reg_junk.zip':
			{
				'test.txt'
			},
			'/media/Storage/Scripts/Deduper/Tests/test_ptree/z_sml.zip':
			{
				'test.txt'
			},
		}

		self.assertEqual(ck.getPhashMatchingArchives(), p_expect)

	def test_junkFileFiltering(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		print(ck.getBestBinaryMatch())
		print(ck.getBestPhashMatch())

		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))


