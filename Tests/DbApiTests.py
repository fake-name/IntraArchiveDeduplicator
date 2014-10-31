
import dbApi
import unittest
import logSetup

class TestDb(dbApi.DbApi):
	tableName = 'testitems'



	def __init__(self, tableName = None, *args, **kwargs):
		if tableName:
			self.tableName = self.tableName+"_"+tableName
		super().__init__(*args, **kwargs)


	def tearDown(self):
		self.log.info("Dropping testing table '{table}'".format(table=self.tableName))
		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		cur = self.conn.cursor()
		cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
		cur.execute("COMMIT;")


TEST_DATA = [
	{"fspath" : '/test/dir1',       "internalpath" : 'item1', "itemhash" : 'DEAD', "phash" : 12,       "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item2', "itemhash" : 'BEEF', "phash" : 6,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item3', "itemhash" : 'CAFE', "phash" : 2,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item4', "itemhash" : 'BABE', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir3',       "internalpath" : 'item0', "itemhash" : 'BABE', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir4',       "internalpath" : 'item0', "itemhash" : 'BABC', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : '',      "itemhash" : '1234', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir2',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir5',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'LOL',   "itemhash" : '6666', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/HERP',  "internalpath" : 'LOL',   "itemhash" : '5555', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50}
]

KEY_ORDER = ["fspath", "internalpath", "itemhash", "phash", "dhash", "itemkind", "imgx", "imgy"]

# TODO: Actual test-failure comments!
class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):

		self.addCleanup(self.dropDatabase)


		self.db = TestDb()
		for testRow in TEST_DATA:
			self.db.insertIntoDb(**testRow)

		# Check the table is set up
		self.assertEqual(self.db.getItemNum(), (len(TEST_DATA),),
				'Setup resulted in an incorrect number of items in database!')

	def dropDatabase(self):
		self.db.tearDown()


	def test_getItemsSimple(self):
		items = set(self.db.getItems())

		cnt = 1
		testDat = []
		for row in TEST_DATA:
			testDat.append( (cnt, ) + tuple([row[key] for key in KEY_ORDER]))
			cnt += 1

		items = list(items)
		items.sort()
		self.assertEqual(items, testDat)


	def test_getItems2(self):
		ret = [(1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 50),
				(2, '/test/dir1', 'item2', 'BEEF', 6, 10, 'N/A', 50, 50),
				(3, '/test/dir1', 'item3', 'CAFE', 2, 10, 'N/A', 50, 50),
				(4, '/test/dir1', 'item4', 'BABE', 7, 10, 'N/A', 50, 50),
				(7, '/test/dir1', '', '1234', None, None, 'N/A', 50, 50)]
		self.assertEqual(self.db.getItems(fspath='/test/dir1'), ret)

	def test_getItems3(self):
		ret = [(7, '/test/dir1', '', '1234', None, None, 'N/A', 50, 50),
				(8, '/test/dir2', '', '4607', None, None, 'N/A', 50, 50),
				(9, '/test/dir5', '', '4607', None, None, 'N/A', 50, 50)]

		self.assertEqual(self.db.getItems(internalpath=''), ret)

	def test_getItems4(self):

		ret = [(row['fspath'], row['internalpath'], row['itemhash']) for row in TEST_DATA]
		self.assertEqual(self.db.getItems(wantCols=["fspath", "internalpath", "itemhash"]), ret)

	def test_itemInDB(self):
		self.assertEqual(self.db.itemInDB(),                                                True)
		self.assertEqual(self.db.itemInDB(fspath='/test/dir1'),                             True)
		self.assertEqual(self.db.itemInDB(fspath='/test/dir1WATWAT'),                       False)
		self.assertEqual(self.db.itemInDB(internalpath=''),                                 True)


	def test_basePathInDB(self):
		self.assertEqual(self.db.basePathInDB("/test/dir5"),    True)
		self.assertEqual(self.db.basePathInDB("/test/dir9999"), False)

	def test_numHashInDB(self):
		self.assertEqual(self.db.numHashInDB("BABE"),    True)
		self.assertEqual(self.db.numHashInDB("BABC"),    True)
		self.assertEqual(self.db.numHashInDB("WAT"),     False)

	def test_getByHash(self):
		self.assertEqual(len(self.db.getByHash("BABE")),   2)
		self.assertEqual(len(self.db.getByHash("BABC")),   1)
		self.assertEqual(self.db.getByHash("WAT"),         [])

	def test_getOtherHashes(self):

		self.assertEqual(self.db.getOtherHashes("BABE", '/test/dir1'),
						[('/test/dir3', 'item0', 'BABE')])

		self.assertEqual(self.db.getOtherHashes("BABE", '/test/dir999'),
					[   ('/test/dir1', 'item4', 'BABE'),
						('/test/dir3', 'item0', 'BABE')])

		self.assertEqual(self.db.getOtherHashes("BABC", '/test/dir1'),
						[('/test/dir4', 'item0', 'BABC')])

		self.assertEqual(self.db.getOtherHashes("WAT", "/WAT"),
						[])

	def test_deleteBasePath(self):
		self.db.deleteBasePath('/test/dir1')
		self.assertEqual(self.db.getItemNum(), (6,))
		self.db.deleteBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (6,))
		self.db.deleteLikeBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (2,))


	# As far as I can tell, these calls are unused (and kind of hard to use, actually). Testing for completeness only.
	def test_getDuplicateImages(self):
		self.assertEqual(len(self.db.getDuplicateImages("/test/")),           4)
		self.assertEqual(len(self.db.getDuplicateImages("/test/dir9999")),    0)

	def test_getDuplicateBaseFiles(self):
		self.assertEqual(len(self.db.getDuplicateBaseFiles("/test/")),        2)
		self.assertEqual(len(self.db.getDuplicateBaseFiles("/test/dir9999")), 0)

	def test_getInternalItemsOnBasePath(self):
		# def getInternalItemsOnBasePath(self, basePath):
		self.assertEqual(self.db.getInternalItemsOnBasePath('/test/dir1'),
					[('/test/dir1', 'item1', 'DEAD'),
					 ('/test/dir1', 'item2', 'BEEF'),
					 ('/test/dir1', 'item3', 'CAFE'),
					 ('/test/dir1', 'item4', 'BABE'),
					 ('/test/dir1', '',      '1234')])

	def test_getLikeBasePath(self):
		# def getLikeBasePath(self, basePath):
		# This is bad, and I should feel bad.
		ret1 = tuple([item for item in [tuple([row[key] for key in KEY_ORDER if key != 'itemkind']) for row in TEST_DATA] if "/test" in item[0]])
		ret2 = tuple([item for item in [tuple([row[key] for key in KEY_ORDER if key != 'itemkind']) for row in TEST_DATA] if "/lol"  in item[0]])

		self.assertEqual(self.db.getLikeBasePath("/test"), ret1)
		self.assertEqual(self.db.getLikeBasePath("/lol"),  ret2)

		pass

	def test_moveItem(self):
		# def moveItem(self, oldPath, newPath):
		print("IMPLEMENT ME!")
		pass

	def test_getPhashLikeBasePath(self):
		# def getPhashLikeBasePath(self, basePath):
		print("IMPLEMENT ME!")
		pass
	def test_getPHashes(self):
		# def getPHashes(self, limit=None):
		print("IMPLEMENT ME!")
		pass
	def test_getFileDictLikeBasePath(self):
		# def getFileDictLikeBasePath(self, basePath):
		print("IMPLEMENT ME!")
		pass

	def test_getDHashes(self):
		# def getDHashes(self, limit=None):
		print("IMPLEMENT ME!")
		pass
	def test_updateItem(self):
		# def updateItem(self, basePath, internalPath, itemHash=None, pHash=None, dHash=None, imgX=None, imgY=None):
		print("IMPLEMENT ME!")
		pass


	def test_getItemsOnBasePath(self):
		# def getItemsOnBasePath(self, basePath):
		print("IMPLEMENT ME!")
		pass
	def test_getItemsOnBasePathInternalPath(self):
		# def getItemsOnBasePathInternalPath(self, basePath, internalPath):
		print("IMPLEMENT ME!")
		pass
	def test_getItemNumberOnBasePath(self):
		# def getItemNumberOnBasePath(self, basePath):
		print("IMPLEMENT ME!")
		pass
	def test_aggregateItems(self):
		# def aggregateItems(self, basePath, internalPath, itemHash):
		print("IMPLEMENT ME!")
		pass
	def test_insertAggregate(self):
		# def insertAggregate(self):
		print("IMPLEMENT ME!")
		pass
	def test_getUniqueOnBasePath(self):
		# def getUniqueOnBasePath(self, basePath):
		print("IMPLEMENT ME!")
		pass
	def test_getAllItems(self):
		# def getAllItems(self):
		print("IMPLEMENT ME!")
		pass
	def test_getItemNum(self):
		# def getItemNum(self):
		print("IMPLEMENT ME!")
		pass
	def test_getHashes(self):
		# def getHashes(self, fsPath, internalPath):
		print("IMPLEMENT ME!")
		pass

# Hard to test:
# def getById(self, dbId):
# def getStreamingCursor(self, wantCols=None, where=None, limit=None, **kwargs):

