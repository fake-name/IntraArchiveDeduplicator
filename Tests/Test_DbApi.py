
import dbApi
import unittest
import scanner.logSetup as logSetup
import psycopg2
import test_settings

class TestDb(dbApi.DbApi):


	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS


	tableName = 'testitems'



	def __init__(self, tableName = None, *args, **kwargs):

		# If the last run didn't complete, we will have dangling tables. Tear them down pre-emptively, so it doesn't
		# error out this run.
		try:
			self.tearDown()
		except:
			pass

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

		#And close the DB connection
		self.conn.close()


TEST_DATA = [
	{"fspath" : '/test/dir1',       "internalpath" : 'item1', "itemhash" : 'DEAD', "phash" : 12,       "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 50, "imgy" : 30},
	{"fspath" : '/test/dir1',       "internalpath" : 'item2', "itemhash" : 'BEEF', "phash" : 6,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 51, "imgy" : 31},
	{"fspath" : '/test/dir1',       "internalpath" : 'item3', "itemhash" : 'CAFE', "phash" : 2,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 52, "imgy" : 32},
	{"fspath" : '/test/dir1',       "internalpath" : 'item4', "itemhash" : 'BABE', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 53, "imgy" : 33},
	{"fspath" : '/test/dir3',       "internalpath" : 'item0', "itemhash" : 'BABE', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 54, "imgy" : 34},
	{"fspath" : '/test/dir4',       "internalpath" : 'item0', "itemhash" : 'BABC', "phash" : 7,        "dhash" : 10,       "itemkind" : 'N/A', "imgx" : 55, "imgy" : 35},
	{"fspath" : '/test/dir1',       "internalpath" : '',      "itemhash" : '1234', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 56, "imgy" : 36},
	{"fspath" : '/test/dir2',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 57, "imgy" : 37},
	{"fspath" : '/test/dir5',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 58, "imgy" : 38},
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'LOL',   "itemhash" : '6666', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 59, "imgy" : 39},
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'DURR',  "itemhash" : '6666', "phash" : 90,       "dhash" : 946,      "itemkind" : 'N/A', "imgx" : 60, "imgy" : 40},
	{"fspath" : '/lol/test1/HERP',  "internalpath" : 'LOL',   "itemhash" : '5555', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 61, "imgy" : 41},
	{"fspath" : '/lol/test1/HERP',  "internalpath" : '',      "itemhash" : '5555', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 62, "imgy" : 42}
]

KEY_ORDER = ["fspath", "internalpath", "itemhash", "phash", "dhash", "itemkind", "imgx", "imgy"]

# TODO: Actual test-failure comments!
class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	# Exists solely so I can override it in other test classes
	def getDb(self):
		return TestDb()

	def setUp(self):

		self.addCleanup(self.dropDatabase)

		self.db = self.getDb()
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
		ret = [(1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 30),
				(2, '/test/dir1', 'item2', 'BEEF', 6, 10, 'N/A', 51, 31),
				(3, '/test/dir1', 'item3', 'CAFE', 2, 10, 'N/A', 52, 32),
				(4, '/test/dir1', 'item4', 'BABE', 7, 10, 'N/A', 53, 33),
				(7, '/test/dir1', '', '1234', None, None, 'N/A', 56, 36)]
		self.assertEqual(self.db.getItems(fspath='/test/dir1'), ret)

	def test_getItems3(self):
		ret = [(7, '/test/dir1', '', '1234', None, None, 'N/A', 56, 36),
				(8, '/test/dir2', '', '4607', None, None, 'N/A', 57, 37),
				(9, '/test/dir5', '', '4607', None, None, 'N/A', 58, 38),
				(13, '/lol/test1/HERP', '', '5555', None, None, 'N/A', 62, 42)]

		self.assertEqual(self.db.getItems(internalpath=''), ret)

	def test_getItems4(self):

		ret = [(row['fspath'], row['internalpath'], row['itemhash']) for row in TEST_DATA]
		self.assertEqual(self.db.getItems(wantCols=["fspath", "internalpath", "itemhash"]), ret)

	def test_getItem1(self):
		item = self.db.getItem(fspath='/test/dir1', internalpath='item1')
		expect = (1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 30)
		self.assertEqual(item, expect)

	def test_getItem2(self):
		item = self.db.getItem(fspath='/test/dir1asasddddddd', internalpath='item1WAT')
		expect = []
		self.assertEqual(item, expect)

	def test_getItem3(self):
		self.assertRaises(ValueError, self.db.getItem, fspath='/test/dir1')

	def test_itemInDB(self):
		self.assertEqual(self.db.itemInDB(),                          True)
		self.assertEqual(self.db.itemInDB(fspath='/test/dir1'),       True)
		self.assertEqual(self.db.itemInDB(fspath='/test/dir1WATWAT'), False)
		self.assertEqual(self.db.itemInDB(internalpath=''),           True)


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
		self.assertEqual(self.db.getItemNum(), (8,))
		self.db.deleteBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (8,))
		self.db.deleteLikeBasePath('/test/')
		self.assertEqual(self.db.getItemNum(), (4,))


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
		paths = ['/test', '/lol']

		for testPath in paths:
			ret = [item for item in [tuple([row[key] for key in KEY_ORDER if key != 'itemkind']) for row in TEST_DATA] if item[0].startswith(testPath)]
			self.assertEqual(self.db.getLikeBasePath(testPath), ret)

	def test_moveItem(self):
		# def moveItem(self, oldPath, newPath):

		testPath = '/test/dir4'
		ret = [item for item in [tuple([row[key] for key in KEY_ORDER if key != 'itemkind']) for row in TEST_DATA] if item[0].startswith(testPath)]
		self.assertEqual(self.db.getLikeBasePath(testPath), ret)

		testPath2 = '/test/dir90'
		self.db.moveItem(testPath, testPath2)
		self.assertEqual(self.db.getLikeBasePath(testPath), [])

		ret = [(testPath2, ) + item[1:] for item in ret]
		self.assertEqual(self.db.getLikeBasePath(testPath2), ret)



	def test_getPhashLikeBasePath(self):
		# def getPhashLikeBasePath(self, basePath):
		testPath = '/test/dir1'

		dbRet = self.db.getPhashLikeBasePath(testPath)
		self.assertEqual(dbRet,[(1, 12), (2, 6), (3, 2), (4, 7)])

		testPath = '/test'
		dbRet = self.db.getPhashLikeBasePath(testPath)
		self.assertEqual(dbRet,[(1, 12), (2, 6), (3, 2), (4, 7), (5, 7), (6, 7)])


	def test_getPHashes(self):
		# def getPHashes(self, limit=None):
		cur = self.db.getPHashes()
		dbHashes = cur.fetchall()
		cur.close()

		hashes = [(1, 12), (2, 6), (3, 2), (4, 7), (5, 7), (6, 7), (11, 90)]

		self.assertEqual(hashes, dbHashes)

	def test_getFileDictLikeBasePath(self):
		# def getFileDictLikeBasePath(self, basePath):
		expected = {'/test/dir1':
						[
							{'fsPath': '/test/dir1', 'dbId': 1, 'dHash': 10, 'itemHash': 'DEAD', 'imgy': 30, 'pHash': 12, 'imgx': 50, 'internalPath': 'item1'},
							{'fsPath': '/test/dir1', 'dbId': 2, 'dHash': 10, 'itemHash': 'BEEF', 'imgy': 31, 'pHash': 6, 'imgx': 51, 'internalPath': 'item2'},
							{'fsPath': '/test/dir1', 'dbId': 3, 'dHash': 10, 'itemHash': 'CAFE', 'imgy': 32, 'pHash': 2, 'imgx': 52, 'internalPath': 'item3'},
							{'fsPath': '/test/dir1', 'dbId': 4, 'dHash': 10, 'itemHash': 'BABE', 'imgy': 33, 'pHash': 7, 'imgx': 53, 'internalPath': 'item4'},
							{'fsPath': '/test/dir1', 'dbId': 7, 'dHash': None, 'itemHash': '1234', 'imgy': 36, 'pHash': None, 'imgx': 56, 'internalPath': ''}
						]
					}

		self.assertEqual(self.db.getFileDictLikeBasePath('/test/dir1'), expected)

		expected = {
						'/lol/test1/HERP':
							[

								{'imgx': 61, 'itemHash': '5555', 'dbId': 12, 'dHash': None, 'internalPath': 'LOL', 'fsPath': '/lol/test1/HERP', 'imgy': 41, 'pHash': None},
								{'imgx': 62, 'itemHash': '5555', 'dbId': 13, 'dHash': None, 'internalPath': '', 'fsPath': '/lol/test1/HERP', 'imgy': 42, 'pHash': None}
							],
						'/lol/test1/WAT':
							[
								{'imgx': 59, 'itemHash': '6666', 'dbId': 10, 'dHash': None, 'internalPath': 'LOL', 'fsPath': '/lol/test1/WAT', 'imgy': 39, 'pHash': None},
								{'imgx': 60, 'itemHash': '6666', 'dbId': 11, 'dHash': 946, 'internalPath': 'DURR', 'fsPath': '/lol/test1/WAT', 'imgy': 40, 'pHash': 90}
							]
					}


		self.assertEqual(self.db.getFileDictLikeBasePath('/lol/test1/'), expected)


	def test_getDHashes(self):
		# def getDHashes(self, limit=None):
		cur = self.db.getDHashes()
		dbHashes = cur.fetchall()
		cur.close()

		hashes = [(1, 10), (2, 10), (3, 10), (4, 10), (5, 10), (6, 10), (11, 946)]
		self.assertEqual(hashes, dbHashes)


		cur = self.db.getDHashes(limit=3)
		dbHashes = cur.fetchall()
		cur.close()

		hashes = [(1, 10), (2, 10), (3, 10)]
		self.assertEqual(hashes, dbHashes)

	def test_getHashes(self):
		# def getHashes(self, fsPath, internalPath):
		self.assertEqual(self.db.getHashes('/lol/test1/WAT', ''), (False, False, False))
		self.assertEqual(self.db.getHashes('DERPPPP', ''), (False, False, False))
		self.assertEqual(self.db.getHashes('/lol/test1/WAT', 'DURR'), ('6666', 90, 946))


	def test_getItemsOnBasePath(self):

		keyStrs = ['/test/dir1', '/lol/test1/WAT', '/lol/test1']
		for keyStr in keyStrs:

			expect = []
			for indice, row in enumerate(TEST_DATA):
				if keyStr == row['fspath']:
					expect.append({'dbId': indice+1, 'fsPath': row["fspath"], 'internalPath': row["internalpath"], 'itemhash': row["itemhash"], 'pHash': row['phash'], "imgx" : row['imgx'], "imgy" : row['imgy']})

			ret = self.db.getItemsOnBasePath(keyStr)
			self.assertEqual(ret, expect)

	def test_getItemsOnBasePathInternalPath(self):
		# def getItemsOnBasePathInternalPath(self, basePath, internalPath):

		ret = self.db.getItemsOnBasePathInternalPath('/test/dir1', '')
		self.assertEqual(ret, [{'imgx': 56, 'fsPath': '/test/dir1', 'internalPath': '', 'itemhash': '1234', 'pHash': None, 'dbId': 7, 'imgy': 36}])

		ret = self.db.getItemsOnBasePathInternalPath('/test/dir1', 'item2')
		self.assertEqual(ret, [{'fsPath': '/test/dir1', 'itemhash': 'BEEF', 'internalPath': 'item2', 'imgy': 31, 'imgx': 51, 'dbId': 2, 'pHash': 6}])

		ret = self.db.getItemsOnBasePathInternalPath('/lol/test1/WAT', 'LOL')
		self.assertEqual(ret, [{'internalPath': 'LOL', 'dbId': 10, 'itemhash': '6666', 'pHash': None, 'imgy': 39, 'fsPath': '/lol/test1/WAT', 'imgx': 59}])


	def test_getItemNumberOnBasePath(self):
		# def getItemNumberOnBasePath(self, basePath):

		self.assertEqual(self.db.getItemNumberOnBasePath('/test/dir1'), 5)
		self.assertEqual(self.db.getItemNumberOnBasePath('/lol/test1/WAT'), 2)
		self.assertEqual(self.db.getItemNumberOnBasePath('/HERPADOODLE'), 0)

	def test_getNumberOfPhashes(self):
		self.assertEqual(self.db.getNumberOfPhashes(), 7)
		self.assertEqual(self.db.getNumberOfPhashes(fspath='/test/dir1'), 4)

	def test_getUniqueOnBasePath(self):
		# def getUniqueOnBasePath(self, basePath):
		cur = self.db.getUniqueOnBasePath('/test/')
		ret = cur.fetchall()
		cur.close()
		expect = [
			('/test/dir4',),
			('/test/dir2',),
			('/test/dir5',),
			('/test/dir1',),
			('/test/dir3',)
		]

		self.assertEqual(ret, expect)

		cur = self.db.getUniqueOnBasePath('/lol/')
		ret = cur.fetchall()
		cur.close()

		expect = [
			('/lol/test1/WAT',),
			('/lol/test1/HERP',)
		]
		self.assertEqual(ret, expect)

		cur = self.db.getUniqueOnBasePath('/DERPADOODLE/')
		ret = cur.fetchall()
		cur.close()

		expect = []
		self.assertEqual(ret, expect)

	def test_getAllItems(self):
		# def getAllItems(self):
		cur = self.db.getAllItems()
		ret = cur.fetchall()
		cur.close()

		expect = []
		for row in TEST_DATA:
			expect.append((row["fspath"], row["internalpath"], row["itemhash"]))

		self.assertEqual(ret, expect)


	def test_getItemNum(self):
		# def getItemNum(self):
		self.assertEqual(self.db.getItemNum(), (len(TEST_DATA),))


	def test_updateItem1(self):
		# def updateDbEntry(self, commit=True, **kwargs)

		expect = [(1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

		self.db.updateDbEntry(dbId=1, itemHash='LOLL')


		expect = [(1, '/test/dir1', 'item1', 'LOLL', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

	def test_updateItem2(self):
		# def updateDbEntry(self, commit=True, **kwargs)

		expect = [(1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

		self.db.updateItem('/test/dir1', 'item1', itemHash='LOLL')

		expect = [(1, '/test/dir1', 'item1', 'LOLL', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

	def test_updateItem3(self):
		# def updateDbEntry(self, commit=True, **kwargs)


		expect = [(1, '/test/dir1', 'item1', 'DEAD', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

		self.db.updateDbEntry(fsPath='/test/dir1', itemHash='LOLL')

		expect = [(1, '/test/dir1', 'item1', 'LOLL', 12, 10, 'N/A', 50, 30)]
		ret = self.db.getItems(dbId=1)
		self.assertEqual(ret, expect)

	def test_insertItem(self):


		# def insertItem(self, *args, **kwargs):
		ret = self.db.getItems(fspath='/durr/wat', internalpath='lolercoaster')
		self.assertEqual(ret, [])

		row = {'pHash': None, 'internalPath': 'lolercoaster', 'imgy': 50, 'itemHash': '1234', 'fsPath': '/durr/wat', 'dHash': None, 'imgx': 50}
		self.db.insertItem(**row)

		ret = self.db.getItems(fspath='/durr/wat', internalpath='lolercoaster')

		expect = [(14, '/durr/wat', 'lolercoaster', '1234', None, None, None, 50, 50)]
		self.assertEqual(ret, expect)



	def test_transactionCalls(self):
		# def commit(self):
		# def rollback(self):
		# def begin(self):

		self.db.begin()
		self.db.commit()

		self.db.begin()
		self.db.rollback()

		with self.db.transaction() as cur:
			pass
		with self.db.transaction(commit=False) as cur:
			pass


		self.db.begin()

		with self.db.transaction() as cur:
			pass
		with self.db.transaction(commit=False) as cur:
			pass

		self.db.commit()

		self.assertRaises(psycopg2.ProgrammingError, self.transactionException)


	def transactionException(self):
		with self.db.transaction() as cur:
			cur.execute("WAT WAT?")

	def test_colmapExceptions(self):
		self.assertRaises(ValueError, self.db.keyToCol, "wat")

	def test_getExtents(self):
		minId, maxId = self.db.getIdExtents()
		self.assertEqual(minId, 1)
		self.assertEqual(maxId, len(TEST_DATA))

	def test_getRandom(self):
		ret = self.db.getRandomRow()

		rows = []
		for row in TEST_DATA:
			rows.append((row["fspath"], row["internalpath"], row["itemhash"], row["phash"], row["dhash"], row["imgx"], row["imgy"] ))

		self.assertIn(ret, rows)

	def test_getById(self):
		expect = [('/test/dir1', 'item1', 'DEAD')]
		ret = self.db.getById(1)
		self.assertEqual(ret, expect)


	def test_deleteRows1(self):

		self.assertEqual(self.db.getItemNumberOnBasePath('/test/dir1'), 5)
		self.db.deleteDbRows(fspath='/test/dir1', internalpath='item1')
		self.assertEqual(self.db.getItemNumberOnBasePath('/test/dir1'), 4)
		self.db.deleteDbRows(fspath='/test/dir1')
		self.assertEqual(self.db.getItemNumberOnBasePath('/test/dir1'), 0)

		self.assertRaises(ValueError, self.db.deleteDbRows)

	# Hard to test:
	def test_getStreamingCursor(self):
		# def getStreamingCursor(self, wantCols=None, where=None, limit=None, **kwargs):
		print("IMPLEMENT ME!")

