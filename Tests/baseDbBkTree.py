
import dbApi
import traceback
import scanner.fileHasher

import os
import psycopg2
import time
import os.path
import logging
import shutil
import gc
import test_settings

import pyximport
pyximport.install()

SRC_ZIP_PATH  = 'test_ptree_base'
TEST_ZIP_PATH = 'test_ptree'

class TestDbBare(dbApi.DbApi):

	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS

	tableName = 'testitems'


class TestBkPhashDb(TestDbBare):

	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS

	tableName = 'testitems_bk_tree'

	streamChunkSize = 5

	def __init__(self, tableName = None, load_database = True, *args, **kwargs):


		# Create the table twice, because horrible.
		if tableName:
			self.tableName = self.tableName+"_"+tableName
		super().__init__(*args, **kwargs)

		try:
			with self.transaction() as cur:
				cur.execute("BEGIN;")
				self.log.info("Clearing table")
				cur.execute('DELETE FROM {table};'.format(table=self.tableName))
				self.log.info("cleared")
				cur.execute("COMMIT;")

		except psycopg2.Error:
			traceback.print_exc()


		try:
			cur.execute('''CREATE        INDEX {table}_phash_bk_tree_index    ON {table} USING spgist ( phash bktree_ops );'''.format(table=self.tableName))
		except psycopg2.ProgrammingError:
			traceback.print_exc()
			print("Failed to create index?")

	def getWithinDistance(self, target_hash, distance):
		with self.transaction() as cur:

			cur.execute("SELECT dbid FROM {table} WHERE phash <@ (%s, %s);".format(table=self.tableName), (target_hash, distance))
			ret = cur.fetchall()
			ret = set([tmp[0] for tmp in ret])
			print(ret)
			return ret

	def insert(self, node_hash, nodeId, cur=None):
		if cur:
			self.insertIntoDb(cur=cur, phash=node_hash, dbid=nodeId, fspath=nodeId, internalpath=nodeId, itemhash=nodeId)
		else:
			with self.transaction() as cur:
				self.insertIntoDb(cur=cur, phash=node_hash, dbid=nodeId, fspath=nodeId, internalpath=nodeId, itemhash=nodeId)


	def remove(self, node_hash, nodeId):
		self.deleteDbRows(dbid=nodeId)



	def tearDown(self):
		# Have to explicitly delete the tree and the hasher objects, so they don't prevent the table from
		# dropping.

		self.log.info("Dropping testing table '{table}'".format(table=self.tableName))
		with self.transaction() as cur:
			self.log.info("Doing drop")
			cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
			self.log.info("Committing")
			cur.execute("COMMIT;")
