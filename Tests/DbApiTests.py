
import dbApi
import unittest
import logSetup

class TestDb(dbApi.DbApi):
	tableName = 'testitems'



	def tearDown(self):
		self.log.info("Dropping testing table '{table}'".format(table=self.tableName))
		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		cur = self.conn.cursor()
		cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
		cur.execute("COMMIT;")


TEST_DATA = [
	{"fspath" : '/test/dir1', "internalpath" : 'item1', "itemhash" : 'DEAD', "phash" : '1101', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir1', "internalpath" : 'item2', "itemhash" : 'BEEF', "phash" : '1001', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir1', "internalpath" : 'item3', "itemhash" : 'CAFE', "phash" : '1011', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir1', "internalpath" : 'item4', "itemhash" : 'BABE', "phash" : '0101', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir3', "internalpath" : 'item0', "itemhash" : 'BABE', "phash" : '0101', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir4', "internalpath" : 'item0', "itemhash" : 'BABC', "phash" : '0101', "dhash" : '1011', "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir1', "internalpath" : '',      "itemhash" : '1234', "phash" : '',     "dhash" : '',     "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir2', "internalpath" : '',      "itemhash" : '4607', "phash" : '',     "dhash" : '',     "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'},
	{"fspath" : '/test/dir5', "internalpath" : '',      "itemhash" : '4607', "phash" : '',     "dhash" : '',     "itemkind" : 'N/A', "imgx" : '50', "imgy" : '50'}
]

# TODO: Actual test-failure comments!
class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.db = TestDb()
		for testRow in TEST_DATA:
			self.db.insertIntoDb(**testRow)

		# Check the table is set up
		self.assertEqual(self.db.getItemNum(), (len(TEST_DATA),),
				'Setup resulted in an incorrect number of items in database!')

	def test_getItems(self):
		self.assertEqual(len(self.db.getItems()),                                                len(TEST_DATA))
		self.assertEqual(len(self.db.getItems(fspath='/test/dir1')),                             5)
		self.assertEqual(len(self.db.getItems(internalpath='')),                                 3)
		self.assertEqual(len(self.db.getItems(wantCols=["fspath", "internalpath", "itemhash"])), len(TEST_DATA))

	def test_itemInDB(self):
		self.assertEqual(self.db.itemInDB(),                                                (len(TEST_DATA),))
		self.assertEqual(self.db.itemInDB(fspath='/test/dir1'),                             (5,))
		self.assertEqual(self.db.itemInDB(internalpath=''),                                 (3,))


	def test_basePathInDB(self):
		self.assertEqual(self.db.basePathInDB("/test/dir5"),    (1, ))
		self.assertEqual(self.db.basePathInDB("/test/dir9999"), (0, ))

	def test_numHashInDB(self):
		self.assertEqual(self.db.numHashInDB("BABE"),    (2, ))
		self.assertEqual(self.db.numHashInDB("BABC"),    (1, ))
		self.assertEqual(self.db.numHashInDB("WAT"),     (0, ))

	def test_getByHash(self):
		self.assertEqual(len(self.db.getByHash("BABE")),   2)
		self.assertEqual(len(self.db.getByHash("BABC")),   1)
		self.assertEqual(self.db.getByHash("WAT"),         [])

	def test_getOtherHashes(self):
		self.assertEqual(len(self.db.getOtherHashes("BABE", '/test/dir1')),   1)
		self.assertEqual(len(self.db.getOtherHashes("BABE", '/test/dir999')), 2)
		self.assertEqual(len(self.db.getOtherHashes("BABC", '/test/dir1')),   1)
		self.assertEqual(self.db.getOtherHashes("WAT", "/WAT"),               [])

	def test_deleteBasePath(self):
		self.db.deleteBasePath('/test/dir1')
		self.assertEqual(self.db.getItemNum(), (4,))
		self.db.deleteBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (4,))
		self.db.deleteLikeBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (0,))


	def tearDown(self):
		self.db.tearDown()




	# As far as I can tell, these calls are unused (and kind of hard to use, actually). Testing for completeness only.
	def test_getDuplicatePhashes(self):
		self.assertEqual(len(self.db.getDuplicatePhashes("/test/")),          3)
		self.assertEqual(len(self.db.getDuplicatePhashes("/test/dir9999")),   0)

	def test_getDuplicateImages(self):
		self.assertEqual(len(self.db.getDuplicateImages("/test/")),           4)
		self.assertEqual(len(self.db.getDuplicateImages("/test/dir9999")),    0)

	def test_getDuplicateBaseFiles(self):
		self.assertEqual(len(self.db.getDuplicateBaseFiles("/test/")),        2)
		self.assertEqual(len(self.db.getDuplicateBaseFiles("/test/dir9999")), 0)



# def getOtherHashes(self, itemHash, fsMaskPath):
# def getOtherDPHashes(self, dHash, pHash, fsMaskPath):
# def getOtherDHashes(self, dHash, fsMaskPath):
# def getOtherPHashes(self, pHash, fsMaskPath):
# def moveItem(self, oldPath, newPath):
# def getPhashLikeBasePath(self, basePath):
# def getPHashes(self, limit=None):
# def getLikeBasePath(self, basePath):
# def getFileDictLikeBasePath(self, basePath):

# def getDHashes(self, limit=None):
# def updateItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None, imgX=None, imgY=None):


# def getItemsOnBasePath(self, basePath):
# def getItemsOnBasePathInternalPath(self, basePath, internalPath):
# def getItemNumberOnBasePath(self, basePath):
# def getInternalItemsOnBasePath(self, basePath):
# def aggregateItems(self, basePath, internalPath, itemHash):
# def insertAggregate(self):
# def getUniqueOnBasePath(self, basePath):
# def getAllItems(self):
# def getItemNum(self):
# def getHashes(self, fsPath, internalPath):

# Hard to test:
# def getById(self, dbId):
# def getStreamingCursor(self, wantCols=None, where=None, limit=None, **kwargs):

