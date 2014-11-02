
import dbPhashApi
import unittest
import scanner.logSetup as logSetup
import psycopg2
from scanner.unitConverters import binStrToInt as b2i

class TestDb(dbPhashApi.PhashDbApi):
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
	{"fspath" : '/test/dir1',       "internalpath" : 'item1', "itemhash" : 'DEAD', "phash" : H_1,      "dhash" : H_7,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item2', "itemhash" : 'BEEF', "phash" : H_2,      "dhash" : H_7,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item3', "itemhash" : 'CAFE', "phash" : H_3,      "dhash" : H_7,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : 'item4', "itemhash" : 'BABE', "phash" : H_4,      "dhash" : H_8,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir3',       "internalpath" : 'item0', "itemhash" : 'BABE', "phash" : H_5,      "dhash" : H_8,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir4',       "internalpath" : 'item0', "itemhash" : 'BABC', "phash" : H_5,      "dhash" : H_8,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir1',       "internalpath" : '',      "itemhash" : '1234', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir2',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/test/dir5',       "internalpath" : '',      "itemhash" : '4607', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'LOL',   "itemhash" : '6666', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/WAT',   "internalpath" : 'DURR',  "itemhash" : '6666', "phash" : H_6,      "dhash" : H_9,      "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/HERP',  "internalpath" : 'LOL',   "itemhash" : '5555', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50},
	{"fspath" : '/lol/test1/HERP',  "internalpath" : '',      "itemhash" : '5555', "phash" : None,     "dhash" : None,     "itemkind" : 'N/A', "imgx" : 50, "imgy" : 50}
]

KEY_ORDER = ["fspath", "internalpath", "itemhash", "phash", "dhash", "itemkind", "imgx", "imgy"]


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
