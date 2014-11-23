
import dbApi
import unittest
import scanner.logSetup as logSetup
import os.path
import scanner.hashFile as hashFile
import UniversalArchiveInterface as uar
import sys

# Brute force random test n database values to ensure their
# values match the ones on disk properly.
# Useful for verifying things like double-checking things like altering the
# low-level hash manipulation routines have not broken anything.
class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)

	def setUp(self):
		self.db = dbApi.DbApi()



	def singleRowTest(self):
		fspath, internalpath, itemhash, phash, dhash, imgx, imgy = self.db.getRandomRow()
		if not (phash and dhash):
			return False
		if not internalpath:
			return False
		if not os.path.exists(fspath):
			print("Item is missing!")
			return False


		with open(fspath, "rb") as fp:
			archCont = fp.read()
		testHash = hashFile.getMd5Hash(archCont)

		archHash = self.db.getItems(wantCols=["itemHash"], fspath=fspath, internalpath='')
		if not archHash:
			print("Could not find archive MD5? Wat")
			print("FsPath", fspath)
			raise ValueError("Wat?")

		archHash = archHash[0][0]

		if not archHash == testHash:
			print("Failure to match overall archive hash!")
			print("Archive", fspath)
			print(testHash, archHash)
			return

		print(".", end='')
		sys.stdout.flush()

		arch = uar.ArchiveReader(fspath, fileContents=archCont)
		fcont = arch.read(internalpath)

		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(fspath, internalpath, fcont)

		self.assertEqual(hexHash, itemhash)
		self.assertEqual(phash, pHash)
		self.assertEqual(dhash, dHash)
		# self.assertEqual(imgx, imX)
		# self.assertEqual(imgy, imY)

		arch.close()
		return True

	def test_getItemsSimple(self):
		x = 0
		while x < 10:
			ret = self.singleRowTest()
			if ret:
				x += 1

