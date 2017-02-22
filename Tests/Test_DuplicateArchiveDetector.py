
import unittest
import pprint
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
			row = list(row)
			row[1] = row[1].replace("/media/Storage/Scripts/Deduper/Tests", "{cwd}")
			print('	%s, ' % list(row))

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
		self.assertFalse(ck.isBinaryUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))
		self.assertTrue(ck.isBinaryUnique())


	def test_isPhashUnique(self):
		cwd = os.path.dirname(os.path.realpath(__file__))


		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))
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
		ck = TestArchiveChecker('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertFalse(ck.getBestPhashMatch())

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		# We default towards the file with the largest common set.
		# if two files have the same common set, the larger file is picked.
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))


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



	def test_getAllMatches_1(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),
			{
				'{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd):
				{
					'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',
					'funny-pictures-cat-looks-like-an-owl.jpg',
					'funny-pictures-cat-will-do-science.jpg',
					'funny-pictures-kitten-rules-a-tower.jpg'
				},
				'{cwd}/test_ptree/small_and_regular.zip'.format(cwd=cwd):
				{
					'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',
					'funny-pictures-cat-looks-like-an-owl.jpg',
					'funny-pictures-cat-will-do-science.jpg',
					'funny-pictures-kitten-rules-a-tower.jpg'
				},
				'{cwd}/test_ptree/small_and_regular_half_common.zip'.format(cwd=cwd):
				{
					'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',
					'funny-pictures-cat-looks-like-an-owl.jpg'
				}
			}
		)
		expect = ck.getPhashMatchingArchives()
		self.assertEqual(expect,
			{
				'{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd):
				{
					('e61ec521-155d-4a3a-956d-2544d4367e02.jpg', 'e61ec521-155d-4a3a-956d-2544d4367e02.jpg'): True,
					('funny-pictures-cat-looks-like-an-owl.jpg', 'funny-pictures-cat-looks-like-an-owl.jpg'): True,
					('funny-pictures-cat-will-do-science.jpg', 'funny-pictures-cat-will-do-science.jpg'): True,
					('funny-pictures-kitten-rules-a-tower.jpg', 'funny-pictures-kitten-rules-a-tower.jpg'): True
				},
				'{cwd}/test_ptree/small_and_regular.zip'.format(cwd=cwd):
				{
					('e61ec521-155d-4a3a-956d-2544d4367e02.jpg', 'e61ec521-155d-4a3a-956d-2544d4367e02.jpg'): True,
					('funny-pictures-cat-looks-like-an-owl.jpg', 'funny-pictures-cat-looks-like-an-owl.jpg'): True,
					('funny-pictures-cat-will-do-science.jpg', 'funny-pictures-cat-will-do-science.jpg'): True,
					('funny-pictures-kitten-rules-a-tower.jpg', 'funny-pictures-kitten-rules-a-tower.jpg'): True
				},
				'{cwd}/test_ptree/small_and_regular_half_common.zip'.format(cwd=cwd):
				{
					('e61ec521-155d-4a3a-956d-2544d4367e02.jpg', 'e61ec521-155d-4a3a-956d-2544d4367e02.jpg'): True,
					('funny-pictures-cat-looks-like-an-owl.jpg', 'funny-pictures-cat-looks-like-an-owl.jpg'): True
				}}
			)

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})
		self.assertEqual(ck.getPhashMatchingArchives(), {})



	def test_getAllMatches_2(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertEqual(ck.getMatchingArchives(),      {})

		expect = {
			'{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd):
				{
					('superheroes-batman-superman-i-would-watch-the-hell-out-of-this.jpg', 'superheroes-batman-superman-i-would-watch-the-hell-out-of-this.jpg'): True,
					('funny-pictures-kitten-rules-a-tower-ps.png', 'funny-pictures-kitten-rules-a-tower-ps.png'): True,
					('funny-pictures-cat-will-do-science-ps.png', 'funny-pictures-cat-will-do-science-ps.png'): True,
					('e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png'): True,
					('funny-pictures-cat-looks-like-an-owl-ps.png', 'funny-pictures-cat-looks-like-an-owl-ps.png'): True
				},
			'{cwd}/test_ptree/small_and_regular.zip'.format(cwd=cwd):
				{
					('funny-pictures-kitten-rules-a-tower-ps.png', 'funny-pictures-kitten-rules-a-tower-ps.png'): True,
					('funny-pictures-cat-will-do-science-ps.png', 'funny-pictures-cat-will-do-science-ps.png'): True,
					('e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png'): True,
					('funny-pictures-cat-looks-like-an-owl-ps.png', 'funny-pictures-cat-looks-like-an-owl-ps.png'): True
				},
			'{cwd}/test_ptree/regular.zip'.format(cwd=cwd):
				{
					('funny-pictures-kitten-rules-a-tower-ps.png', 'funny-pictures-kitten-rules-a-tower-ps.png'): True,
					('funny-pictures-cat-will-do-science-ps.png', 'funny-pictures-cat-will-do-science-ps.png'): True,
					('e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png'): True,
					('funny-pictures-cat-looks-like-an-owl-ps.png', 'funny-pictures-cat-looks-like-an-owl-ps.png'): True
				},
			'{cwd}/test_ptree/small_and_regular_half_common.zip'.format(cwd=cwd):
				{
					('e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png'): True,
					('funny-pictures-cat-looks-like-an-owl-ps.png', 'funny-pictures-cat-looks-like-an-owl-ps.png'): True}



		}

		match = ck.getPhashMatchingArchives()
		print("Match:")
		print(match)
		print()
		self.assertEqual(expect, match)



	def test_getAllMatches_3(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		match_expected = {
			'{cwd}/test_ptree/z_sml_u.zip'.format(cwd=cwd):
			{
				'129165237051396578(s).jpg'
			},
			'{cwd}/test_ptree/z_sml_w.zip'.format(cwd=cwd):
			{
				'test.txt'
			},
			'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd):
			{
				'test.txt'
			}
		}

		pmatch_expected = {
				'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd):
					{
						('129165237051396578(s).jpg', '129165237051396578(s).jpg'): True,
						('test.txt', 'test.txt'): True
					},
				'{cwd}/test_ptree/z_sml_u.zip'.format(cwd=cwd):
					{
						('129165237051396578(s).jpg', '129165237051396578(s).jpg'): True
					},
				'{cwd}/test_ptree/z_sml_w.zip'.format(cwd=cwd):
					{
						('test.txt', 'test.txt'): True
					}
			}



		match = ck.getMatchingArchives()
		self.assertEqual(match,      match_expected)

		actual_pmatch = ck.getPhashMatchingArchives()
		self.assertEqual(actual_pmatch, pmatch_expected)


	def test_getAllMatches_4(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# The `notQuiteAllArch` has both binary and phash duplicates (since phash duplicates
		# are a superset of binary duplicates, if you have binary duplicates, you by definition
		# must have phash duplicates.)
		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		match_expected = {
			'{cwd}/test_ptree/testArch.zip'.format(cwd=cwd):
				{
					'Lolcat_this_is_mah_job.png',
					'Lolcat_this_is_mah_job_small.jpg'
				},
			'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd):
				{
					'Lolcat_this_is_mah_job.jpg',
					'lolcat-crocs.jpg',
					'Lolcat_this_is_mah_job.png',
					'Lolcat_this_is_mah_job_small.jpg',
					'lolcat-oregon-trail.jpg'
				}
			}
		pmatch_expected = {
			'{cwd}/test_ptree/testArch.zip'.format(cwd=cwd):
				{
					('Lolcat_this_is_mah_job.jpg', 'Lolcat_this_is_mah_job.jpg'): True,
					('Lolcat_this_is_mah_job.png', 'Lolcat_this_is_mah_job.png'): True,
					('Lolcat_this_is_mah_job_small.jpg', 'Lolcat_this_is_mah_job_small.jpg'): True
				},
			'{cwd}/test_ptree/allArch.zip'.format(cwd=cwd):
				{
					('Lolcat_this_is_mah_job.jpg', 'Lolcat_this_is_mah_job.jpg'): True,
					('Lolcat_this_is_mah_job.png', 'Lolcat_this_is_mah_job.png'): True,
					('Lolcat_this_is_mah_job_small.jpg', 'Lolcat_this_is_mah_job_small.jpg'): True,
					('lolcat-crocs.jpg', 'lolcat-crocs.jpg'): True,
					('lolcat-oregon-trail.jpg', 'lolcat-oregon-trail.jpg'): True
				}
			}


		match  = ck.getMatchingArchives()
		pmatch = ck.getPhashMatchingArchives()

		pprint.pprint(pmatch)

		self.assertEqual(match,  match_expected)
		self.assertEqual(pmatch, pmatch_expected)

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
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))

		# Remove the matching arch
		os.remove('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		os.remove('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))

		# Verify the match now fails
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		val = ck.getBestPhashMatch()
		pprint.pprint(val)
		self.assertFalse(val)


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
		test_skipSolid()

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
			'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd):
			{
				('test.txt', 'test.txt'): True
			},
			'{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd):
			{
				('test.txt', 'test.txt'): True
			},
			'{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd):
			{
				('test.txt', 'test.txt'): True
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


	def test_addArchive(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)
		self.db.deleteBasePath(archPath)

		self.assertFalse(self.db.getLikeBasePath(archPath))
		self.assertFalse(self.db.getItems(fspath=archPath))

		ck = TestArchiveChecker(archPath)
		ck.addArch()

		# Build a list of items from CONTENTS where the fspath
		# is the archive we just added, chop off the DBID (because that'll
		# have changed), add to a list
		expect = []
		for item in CONTENTS:
			if item[1] == archPath:
				expect.append(list(item[1:]))

		# Get all the items that were just added, chop off the dbid.
		have = self.db.getItems(fspath=archPath)
		have = [list(item[1:]) for item in have]

		have.sort()
		expect.sort()

		self.assertEqual(have, expect)

	def test_deleteArchive_1(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)

		ck = TestArchiveChecker(archPath)
		ck.deleteArch()

		self.assertFalse(os.path.exists(archPath))


	def test_deleteArchive_2(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)

		ck = TestArchiveChecker(archPath)
		ck.deleteArch(moveToPath=os.path.join(cwd, 'test_ptree'))

		self.assertFalse(os.path.exists(archPath))

		toPath = archPath.replace("/", ';')
		toPath = os.path.join(cwd, 'test_ptree', toPath)
		self.assertTrue(os.path.exists(toPath))



	def test_deleteArchive_3(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)

		ck = TestArchiveChecker(archPath)

		self.assertTrue(os.path.exists(archPath))
		ck.deleteArch(moveToPath='/this/path/does/not/exist')
		self.assertTrue(os.path.exists(archPath))


	def test_isArchive(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd)

		self.assertTrue(TestArchiveChecker.isArchive(archPath))
		with open('{cwd}/test_ptree/testTextFile.zip'.format(cwd=cwd), 'w') as fp:
			fp.write("testing\n")
			fp.write("file!\n")
		self.assertFalse(TestArchiveChecker.isArchive('{cwd}/test_ptree/testTextFile.zip'.format(cwd=cwd)))


	def test_addArchive_1(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = '{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd)

		status, bestMatch, commonArches = deduplicator.ProcessArchive.processDownload(archPath, checkClass=TestArchiveChecker)
		matchPath = '{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd)
		self.assertEqual(status, 'deleted was-duplicate')
		self.assertEqual(bestMatch, matchPath)
		expect = {
			2:
				[
					'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd),
					'{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd)
				]
		}
		self.assertEqual(commonArches, expect)

	def test_addArchive_2(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		archPath = '{cwd}/test_ptree/small.zip'.format(cwd=cwd)

		status, bestMatch, commonArches = deduplicator.ProcessArchive.processDownload(archPath, checkClass=TestArchiveChecker)
		matchPath = '{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd)
		self.assertEqual(status, 'deleted was-duplicate phash-duplicate')
		self.assertEqual(bestMatch, matchPath)
		expect = {

			4: [
				'/media/Storage/Scripts/Deduper/Tests/test_ptree/regular.zip',
				'/media/Storage/Scripts/Deduper/Tests/test_ptree/small_and_regular.zip'
				],
			 5: [
			 		'/media/Storage/Scripts/Deduper/Tests/test_ptree/regular-u.zip'
			 	]

		}
		self.assertEqual(commonArches, expect)

	def test_addArchive_3(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		os.remove('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))
		os.remove('{cwd}/test_ptree/small_and_regular.zip'.format(cwd=cwd))

		archPath = '{cwd}/test_ptree/regular.zip'.format(cwd=cwd)

		status, bestMatch, commonArches = deduplicator.ProcessArchive.processDownload(archPath, checkClass=TestArchiveChecker)


		expect = {
			2: ['{cwd}/test_ptree/small_and_regular_half_common.zip'.format(cwd=cwd)]
		}

		self.assertFalse(status)
		self.assertFalse(bestMatch)
		self.assertEqual(commonArches, expect)


	def test_addArchive_4(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		archPath = '{cwd}/lol/wat/herp/derp.zip'.format(cwd=cwd)

		status, bestMatch, commonArches = deduplicator.ProcessArchive.processDownload(archPath, checkClass=TestArchiveChecker)

		self.assertEqual(status, 'damaged')
		self.assertFalse(bestMatch)

		# IF the archive can't be scanned, no duplicates will be found.
		self.assertEqual(commonArches, {})


	# There was a failing issue when a returned phash has no resolution entry.
	# I thought I had fixed those in the DB, but I guess not
	# Add a test to verify this is fixed.
	def test_missingResolutionData(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Remove junk zip so z_reg is actually unique
		os.remove('{cwd}/test_ptree/z_reg_junk.zip'.format(cwd=cwd))

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd))

		rows = []
		rows.extend(self.db.getLikeBasePath('{cwd}/test_ptree/regular.zip'.format(cwd=cwd)))
		rows.extend(self.db.getLikeBasePath('{cwd}/test_ptree/regular-u.zip'.format(cwd=cwd)))

		# Mask out all the rows without phash values.
		rows = [row for row in rows if row[3]]
		rows.sort()

		# Set all the image sizes to NULL
		for row in rows:
			fsPath, intPath = row[0], row[1]
			self.db.updateDbEntry(fsPath=fsPath, internalPath=intPath, imgx=None, imgy=None)

		# Check that we get no match
		self.assertFalse(ck.getBestPhashMatch())
