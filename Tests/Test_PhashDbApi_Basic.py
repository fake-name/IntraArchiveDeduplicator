
import dbPhashApi
import unittest
import scanner.logSetup as logSetup
import psycopg2

import Tests.Test_DbApi
import test_settings




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

class TestDb(dbPhashApi.PhashDbApi):


	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS


	tableName = 'testitems'



	def __init__(self, tableName = None, *args, **kwargs):

		self.connect()

		# If the last run didn't complete, we will have dangling tables. Tear them down pre-emptively, so it doesn't
		# error out this run.
		try:
			self.tearDown()
		except:
			pass


		if tableName:
			self.tableName = self.tableName+"_"+tableName

		super().__init__(*args, **kwargs)



		for testRow in TEST_DATA:
			print("Inserting", testRow)
			self.insertIntoDb(**testRow)



	def tearDown(self):
		print("Dropping testing table '{table}'".format(table=self.tableName))
		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		cur = self.conn.cursor()
		cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
		cur.execute("COMMIT;")

		#And close the DB connection
		# self.conn.close()
class TestSequenceFunctions(Tests.Test_DbApi.TestSequenceFunctions):

	# Swap out the db class
	def getDb(self):
		return TestDb()
