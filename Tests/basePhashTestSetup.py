
import dbPhashApi
import scanner.fileHasher

import os
import os.path
import logging

import pyximport
pyximport.install()

TEST_ZIP_PATH = 'test_ptree'

class TestDbBare(dbPhashApi.PhashDbApi):
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
	tableName = 'testitems'

	streamChunkSize = 5

	def __init__(self, tableName = None, *args, **kwargs):
		print("TestDbStarting")
		if tableName:
			self.tableName = self.tableName+"_"+tableName
		super().__init__(*args, **kwargs)

		self.tree.dropTree()
		self.hasher = TestHasher()

		self.load_zips(TEST_ZIP_PATH)

		# Since the tree deliberately persists (it's a singleton), we have to /explicitly/ clobber it.
		self.tree.dropTree()
		self.doLoad()

	def load_zips(self, dirPath):
		cwd = os.path.dirname(os.path.realpath(__file__))

		for item in os.listdir(os.path.join(cwd, dirPath)):
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


