
import dbPhashApi
import scanner.fileHasher

import os
import os.path
import logging
import shutil
import test_settings

import pyximport
pyximport.install()

SRC_ZIP_PATH  = 'test_ptree_base'
TEST_ZIP_PATH = 'test_ptree'

class TestDbBare(dbPhashApi.PhashDbApi):

	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS

	tableName = 'testitems'

# Need to override the database in the hasher.
class TestHasher(scanner.fileHasher.HashThread):

	loggerPath = "Main.HashEngine"

	def __init__(self):

		self.tlog = logging.getLogger(self.loggerPath)
		self.archIntegrity = True
		self.dbApi = TestDbBare(noglobal=True)

	# Nop the progress bar output
	def putProgQueue(self, value):
		pass

class TestDb(TestDbBare):

	_psqlDbIpAddr = test_settings.PSQL_IP
	_psqlDbName   = test_settings.PSQL_DB_NAME
	_psqlUserName = test_settings.PSQL_USER
	_psqlUserPass = test_settings.PSQL_PASS

	tableName = 'testitems'

	streamChunkSize = 5

	def __init__(self, tableName = None, load_database = True, *args, **kwargs):

		if tableName:
			self.tableName = self.tableName+"_"+tableName
		super().__init__(*args, **kwargs)

		self.hasher = TestHasher()

		if load_database:
			self.copy_zips()

			self.tree.dropTree()

			self.log.info("sync()ing")
			# You need an explicit sync call or the load_zips call can sometimes miss the new files.
			# Yes, this was actually an issue.
			os.sync()

			self.load_zips(TEST_ZIP_PATH)

			# Since the tree deliberately persists (it's a singleton), we have to /explicitly/ clobber it.
			self.tree.dropTree()
			self.doLoad()

	def copy_zips(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		srcPath = os.path.join(cwd, SRC_ZIP_PATH)
		tmpPath = os.path.join(cwd, TEST_ZIP_PATH)
		if not os.path.exists(tmpPath):
			os.mkdir(tmpPath)

		for item in os.listdir(srcPath):
			srcitem = os.path.join(srcPath, item)
			dstitem = os.path.join(tmpPath, item)
			shutil.copy(srcitem, dstitem)

	def load_zips(self, dirPath):
		cwd = os.path.dirname(os.path.realpath(__file__))
		items = os.listdir(os.path.join(cwd, dirPath))

		# Make database-ordering deterministic
		items.sort()
		for item in items:
			item = os.path.join(cwd, dirPath, item)
			self.hasher.processArchive(item)

	def tearDown(self):
		# Have to explicitly delete the tree and the hasher objects, so they don't prevent the table from
		# dropping.
		del self.tree
		del self.hasher

		self.log.info("Dropping testing table '{table}'".format(table=self.tableName))
		cur = self.conn.cursor()
		cur.execute("BEGIN;")
		self.log.info("Doing drop")
		cur.execute('DROP TABLE {table} CASCADE;'.format(table=self.tableName))
		self.log.info("Committing")
		cur.execute("COMMIT;")


		cwd = os.path.dirname(os.path.realpath(__file__))
		tmpPath = os.path.join(cwd, TEST_ZIP_PATH)
		for item in os.listdir(tmpPath):
			dstitem = os.path.join(tmpPath, item)
			os.remove(dstitem)
		os.rmdir(tmpPath)
