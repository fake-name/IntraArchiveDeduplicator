
import dbPhashApi
import unittest
import scanner.logSetup as logSetup
import psycopg2
from scanner.unitConverters import binStrToInt as b2i

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb
import test_settings

class TestDb(dbPhashApi.PhashDbApi):


	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS

	tableName = 'testitems'

	streamChunkSize = 1

	def __init__(self, tableName = None, *args, **kwargs):
		if tableName:
			self.tableName = self.tableName+"_"+tableName
		super().__init__(*args, **kwargs)

		# Since the tree deliberately persists (it's a singleton), we have to /explicitly/ clobber it.
		self.tree.dropTree()
		self.doLoad()

	def tearDown(self):
		self.log.info("Dropping testing table '{table}'".format(table=self.tableName))
		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		cur = self.conn.cursor()
		cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
		cur.execute("COMMIT;")


# Define hashes as binary so they're easier to understand
H_1 = b2i("0000000000000000000000000000000000000000000000000000000000000000")
H_2 = b2i("1111111111111111111111111111111111111111111111111111111111111111")
H_3 = b2i("1000000000000000000000000000000000000000000000000000000000000000")
H_4 = b2i("0111111111111111111111111111111111111111111111111111111111111111")
H_5 = b2i("1100000000000000000000000000000000000000000000000000000000000000")
H_6 = b2i("0100000000000000000000000000000000000000000000000000000000000000")
H_7 = b2i("0000000000000000000000000000000000000001111111111111111000000000")
H_8 = b2i("0000000000000000000000111100000000000001111111111111111000000000")
H_9 = b2i("0000000000000000000000111100100000000001111111111111111000000000")


TEST_DATA = [
	{"fspath" : '/test/dir1',       "internalpath" : 'item1', "itemhash" : 'DEAD', "phash" : H_1,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 1
	{"fspath" : '/test/dir1',       "internalpath" : 'item2', "itemhash" : 'BEEF', "phash" : H_2,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 2
	{"fspath" : '/test/dir1',       "internalpath" : 'item3', "itemhash" : 'CAFE', "phash" : H_3,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 3
	{"fspath" : '/test/dir1',       "internalpath" : 'item4', "itemhash" : 'BABE', "phash" : H_4,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 4
	{"fspath" : '/test/dir3',       "internalpath" : 'item0', "itemhash" : 'BABE', "phash" : H_5,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 5
	{"fspath" : '/test/dir4',       "internalpath" : 'item0', "itemhash" : 'BABC', "phash" : H_5,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 6
	{"fspath" : '/test/dir1',       "internalpath" : '',      "itemhash" : '1234', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}, # 7
	{"fspath" : '/test/dir2',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}, # 8
	{"fspath" : '/test/dir5',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}, # 9
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'LOL',   "itemhash" : '6666', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}, # 10
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'DURR',  "itemhash" : '6666', "phash" : H_6,    "itemkind" : 'N/A', "imgx" : 50,   "imgy" : 50},   # 11
	{"fspath" : '/lol/test1/HERP',  "internalpath" : 'LOL',   "itemhash" : '5555', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}, # 12
	{"fspath" : '/lol/test1/HERP',  "internalpath" : '',      "itemhash" : '5555', "phash" : None,   "itemkind" : 'N/A', "imgx" : None, "imgy" : None}  # 13
]

KEY_ORDER = ["fspath", "internalpath", "itemhash", "phash", "itemkind", "imgx", "imgy"]


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

	def test_treeExists(self):
		self.assertIsInstance(self.db.tree, hamDb.BkHammingTree)


	def test_loadFromDb(self):
		self.db.tree.dropTree()
		self.db.doLoad()


	# Verify the structure of the tree
	# does not change across reloading.
	def test_testLoadingDeterminsm(self):
		loadedTree = list(self.db.tree.root)

		self.db.tree.root = None
		self.db.tree.nodes = 0

		self.db.doLoad()

		self.assertEqual(list(self.db.tree.root), loadedTree)


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


	def test_searchByPhash1(self):

		expect = [
			(1, '/test/dir1',      'item1', 'DEAD',                    0, 'N/A', 50, 50),
			(3, '/test/dir1',      'item3', 'CAFE', -9223372036854775808, 'N/A', 50, 50),
			(11, '/lol/test1/WAT', 'DURR',  '6666',  4611686018427387904, 'N/A', 50, 50),
			(5, '/test/dir3',      'item0', 'BABE', -4611686018427387904, 'N/A', 50, 50),
			(6, '/test/dir4',      'item0', 'BABC', -4611686018427387904, 'N/A', 50, 50),
		]

		ret = self.db.getWithinDistance(H_5)
		self.assertEqual(ret, expect)

		ret = self.db.getWithinDistance(H_6)
		self.assertEqual(ret, expect)

	def test_searchByPhash2(self):
		ret = self.db.getWithinDistance(H_9)
		self.assertEqual(ret, [])


	def test_searchByPhash3(self):
		expect = [
			(2, '/test/dir1', 'item2', 'BEEF',                  -1, 'N/A', 50, 50),
			(4, '/test/dir1', 'item4', 'BABE', 9223372036854775807, 'N/A', 50, 50)
		]

		ret = self.db.getWithinDistance(H_4)
		self.assertEqual(ret, expect)



