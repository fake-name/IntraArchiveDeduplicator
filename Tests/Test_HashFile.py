
import dbApi
import unittest
import scanner.logSetup as logSetup
import os.path
import scanner.hashFile as hashFile
import UniversalArchiveReader as uar
import sys

# Brute force random test n database values to ensure their
# values match the ones on disk properly.
# Useful for verifying things like double-checking things like altering the
# low-level hash manipulation routines have not broken anything.
class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()
		super().__init__(*args, **kwargs)


	def test_getItemsSimple(self):
		x = 0
		while x < 10:
			ret = self.singleRowTest()
			if ret:
				x += 1

