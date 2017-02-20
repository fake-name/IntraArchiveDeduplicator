
import unittest
import scanner.logSetup as logSetup

import deduplicator.ProcessArchive

import Tests.basePhashTestSetup

import os.path
import scanner.fileHasher

import pyximport
pyximport.install()
import deduplicator.cyHamDb as hamDb

from Tests.baseArchiveTestSetup import CONTENTS

# We're testing internal functions, so disable the "accessed <cls>._func()" warning
# pylint: disable=W0212


class TestHasher(scanner.fileHasher.HashThread):

	def getDbConnection(self):
		return Tests.basePhashTestSetup.TestDbBare()

# Override the db connection object in the ArchChecker so it uses the testing database.
class TestArchiveChecker(deduplicator.ProcessArchive.ArchChecker):
	hasher = TestHasher
	def getDbConnection(self):
		return Tests.basePhashTestSetup.TestDbBare()

class TestArchDuplicateFiles(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):

		self.db = Tests.basePhashTestSetup.TestDb(load_database=False)



	def test_archiveOk_1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_duplicate_files.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		with self.assertRaises(deduplicator.ProcessArchive.InvalidArchivePhashContentsException):
			ck._checkHashesOk(fc, 4)


	def test_archiveOk_2(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		ck = TestArchiveChecker('{cwd}/testArches/testArches.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		try:
			ck._checkHashesOk(fc, 4)
		except deduplicator.ProcessArchive.ArchiveProcessorException:
			self.fail("_checkHashesOk() threw an error!")

	def test_archiveOk_3(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_few_duplicate_md5_hashes.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		try:
			ck._checkHashesOk(fc, 4)
		except deduplicator.ProcessArchive.ArchiveProcessorException:
			self.fail("_checkHashesOk() threw an error!")

	def test_archiveOk_4(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_many_duplicate_md5_hashes.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		with self.assertRaises(deduplicator.ProcessArchive.InvalidArchiveMd5ContentsException):
			ck._checkHashesOk(fc, 4)

	def test_archiveOk_5(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_few_duplicate_md5_hashes.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		try:
			ck._checkHashesOk(fc, 4)
		except deduplicator.ProcessArchive.ArchiveProcessorException:
			self.fail("_checkHashesOk() threw an error!")


	def test_archiveOk_6(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_many_duplicate_md5_hashes.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		with self.assertRaises(deduplicator.ProcessArchive.InvalidArchiveMd5ContentsException):
			ck._checkHashesOk(fc, 4)

	def test_archiveOk_7(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_more_duplicate_md5_only.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		with self.assertRaises(deduplicator.ProcessArchive.InvalidArchiveMd5ContentsException):
			ck._checkHashesOk(fc, 4)

	def test_archiveOk_8(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		ck = TestArchiveChecker('{cwd}/testArches/testArches_some_duplicate_md5_only.zip'.format(cwd=cwd))

		fc = ck._loadFileContents()
		try:
			ck._checkHashesOk(fc, 4)
		except deduplicator.ProcessArchive.ArchiveProcessorException:
			self.fail("_checkHashesOk() threw an error!")





