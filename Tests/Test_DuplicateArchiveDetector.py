
import unittest
import scanner.logSetup as logSetup

import deduplicator.ProcessArchive

import Tests.basePhashTestSetup

import os.path

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb

def insertCwd(inStr):
	cwd = os.path.dirname(os.path.realpath(__file__))
	inStr = inStr.format(cwd=cwd)
	return inStr


CONTENTS = [
	[1,  '{cwd}/test_ptree/allArch.zip',         '',                                            '9d7d02a6bff693737904c5d1a35c89cc', None,                 None,                 None, None, None],
	[2,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    -4504585791368671746, None, 493,  389],
	[3,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
	[4,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
	[5,  '{cwd}/test_ptree/allArch.zip',         'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  4576150637722077151,  None, 325,  307],
	[6,  '{cwd}/test_ptree/allArch.zip',         'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, 167400391896309758,   None, 500,  363],
	[7,  '{cwd}/test_ptree/allArch.zip',         'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, -8660145558008088574, None, 501,  356],
	[8,  '{cwd}/test_ptree/notQuiteAllArch.zip', '',                                            'd3c2108bfc69602cfbf2f821eb874ccd', None,                 None,                 None, None, None],
	[9,  '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    -4504585791368671746, None, 493,  389],
	[10, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
	[11, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
	[12, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, 167400391896309758,   None, 500,  363],
	[13, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, -8660145558008088574, None, 501,  356],
	[14, '{cwd}/test_ptree/regular.zip',         '',                                            '215d10a57cfd97756599b4bd93a06655', None,                 None,                 None, None, None],
	[15, '{cwd}/test_ptree/regular.zip',         'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, 5546533486212567551,  None, 500,  375],
	[16, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      -4629305759067799552, None, 492,  442],
	[17, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-will-do-science.jpg',      '5b5620b0cfcb469aef632864707a0445', -6361731780925024615, 1119025673978783491,  None, 500,  674],
	[18, '{cwd}/test_ptree/regular.zip',         'funny-pictures-kitten-rules-a-tower.jpg',     'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, 9187567978625498130,  None, 500,  375],
	[19, '{cwd}/test_ptree/small.zip',           '',                                            'e03de591503f67302f77dad9e0a80669', None,                 None,                 None, None, None],
	[20, '{cwd}/test_ptree/small.zip',           'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, 5546533486212567551,  None, 375,  281],
	[21, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      -4629305759067799552, None, 369,  332],
	[22, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-will-do-science-ps.png',   'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780920830311, 1119025673978783491,  None, 375,  506],
	[23, '{cwd}/test_ptree/small.zip',           'funny-pictures-kitten-rules-a-tower-ps.png',  'fb64248009dde8605a95b041b772544a', -5860684349360469885, 9187567978625498130,  None, 375,  281],
	[24, '{cwd}/test_ptree/testArch.zip',        '',                                            '86975a1f7fca8d520fb0bd4a29b1e953', None,                 None,                 None, None, None],
	[25, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
	[26, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
	[27, '{cwd}/test_ptree/testArch.zip',        'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  4576150637722077151,  None, 325,  307],
	[28, '{cwd}/test_ptree/z_reg.zip',           '',                                            '540b7eb1957fe652db020f67e7dd574a', None,                 None,                 None, None, None],
	[29, '{cwd}/test_ptree/z_reg.zip',           '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, 4593710720968564225,  None, 332,  497],
	[30, '{cwd}/test_ptree/z_sml.zip',           '',                                            '6eac2bd15078c6ce8c412f09d8266abd', None,                 None,                 None, None, None],
	[31, '{cwd}/test_ptree/z_sml.zip',           '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, 4593710720834346496,  None, 249,  373],

]

# Patch in current script directory so the CONTENTS paths work.
curdir = os.path.dirname(os.path.realpath(__file__))
for x in range(len(CONTENTS)):
	CONTENTS[x][1] = CONTENTS[x][1].format(cwd=curdir)
	CONTENTS[x] = tuple(CONTENTS[x])

# Override the db connection object in the ArchChecker so it uses the testing database.
class TestArchiveChecker(deduplicator.ProcessArchive.ArchChecker):
	def getDbConnection(self):
		return Tests.basePhashTestSetup.TestDbBare()

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
		self.db.tree.dropTree()
		self.db.tearDown()

	def verifyDatabaseLoaded(self):
		expect = list(CONTENTS)
		expect.sort()
		items = list(self.db.getItems())
		items.sort()
		self.assertEqual(items, expect)

	def test_getItemsSimple(self):
		self.verifyDatabaseLoaded()


	def test_isBinaryUnique(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		print(ck.isBinaryUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertTrue(ck.isBinaryUnique())

	def test_isPhashUnique(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

		# Check that we're not mis-matching smaller images.
		ck = TestArchiveChecker('{cwd}/test_ptree/regular.zip'.format(cwd=cwd))
		self.assertTrue(ck.isPhashUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))
		self.assertTrue(ck.isPhashUnique())

		# Check that we are properly matching larger images
		ck = TestArchiveChecker('{cwd}/test_ptree/small.zip'.format(cwd=cwd))
		self.assertFalse(ck.isPhashUnique())

		ck = TestArchiveChecker('{cwd}/test_ptree/z_sml.zip'.format(cwd=cwd))
		self.assertFalse(ck.isPhashUnique())


	def test_getBestMatch(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

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
		self.assertFalse(ck.getBestBinaryMatch())
		self.assertEqual(ck.getBestPhashMatch(), '{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd))


		# The `notQuiteAllArch` has both binary and phash duplicates (since phash duplicates
		# are a superset of binary duplicates, if you have binary duplicates, you by definition
		# must have phash duplicates.)
		ck = TestArchiveChecker('{cwd}/test_ptree/notQuiteAllArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestPhashMatch(),  '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))
		self.assertEqual(ck.getBestBinaryMatch(), '{cwd}/test_ptree/allArch.zip'.format(cwd=cwd))

	def test_getAllMatches(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))

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
			'{cwd}/test_ptree/z_reg.zip'.format(cwd=cwd) :
				{
					'129165237051396578.jpg'
				}
			}
		self.assertEqual(ck.getMatchingArchives(),      {})
		self.assertEqual(ck.getPhashMatchingArchives(), match)


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


	def test_itemRemoved(self):
		self.verifyDatabaseLoaded()
		cwd = os.path.dirname(os.path.realpath(__file__))


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


