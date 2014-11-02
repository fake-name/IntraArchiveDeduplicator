
import dbPhashApi
import unittest
import scanner.logSetup as logSetup
import psycopg2

import Tests.Test_DbApi

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

class TestSequenceFunctions(Tests.Test_DbApi.TestSequenceFunctions):

	# Swap out the db class
	def getDb(self):
		return TestDb()
