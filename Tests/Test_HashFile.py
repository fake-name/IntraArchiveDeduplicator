
import unittest
import scanner.hashFile as hashFile
import os.path

# Unit testing driven by lolcat images
# AS GOD INTENDED!

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)


	def test_hashImage1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'dangerous-to-go-alone.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "dcd6097eeac911efed3124374f44085b" )
		self.assertEqual(pHash,   -149413575039568585 )
		self.assertEqual(dHash,   4576150637722077151 )
		self.assertEqual(imX,     325 )
		self.assertEqual(imY,     307)


	def test_hashImage2(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'Lolcat_this_is_mah_job.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "d9ceeb6b43c2d7d096532eabfa6cf482" )
		self.assertEqual(pHash,   27427800275512429 )
		self.assertEqual(dHash,   -4504585791368671746 )
		self.assertEqual(imX,     493 )
		self.assertEqual(imY,     389)


	# check that phash is invariant across format changes
	def test_hashImage2_b(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'Lolcat_this_is_mah_job.png')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "1268e704908cc39299d73d6caafc23a0" )
		self.assertEqual(pHash,   27427800275512429 )
		self.assertEqual(dHash,   -4504585791368671746 )
		self.assertEqual(imX,     493 )
		self.assertEqual(imY,     389)


	# check that phash is invariant across size changes
	def test_hashImage2_c(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'Lolcat_this_is_mah_job_small.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "40d39c436e14282dcda06e8aff367307" )
		self.assertEqual(pHash,   27427800275512429 )
		self.assertEqual(dHash,   -4504585791368671746 )
		self.assertEqual(imX,     300 )
		self.assertEqual(imY,     237)


	def test_hashImage3(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'lolcat-crocs.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "6d0a977694630ac9d1d33a7f068e10f8" )
		self.assertEqual(pHash,   -5569898607211671279 )
		self.assertEqual(dHash,   167400391896309758 )
		self.assertEqual(imX,     500 )
		self.assertEqual(imY,     363)


	def test_hashImage4(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'lolcat-oregon-trail.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "7227289a017988b6bdcf61fd4761f6b9")
		self.assertEqual(pHash,   -4955310669995365332)
		self.assertEqual(dHash,   -8660145558008088574)
		self.assertEqual(imX,     501)
		self.assertEqual(imY,     356)


	def test_hashImage5(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'lolcat-oregon-trail.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "7227289a017988b6bdcf61fd4761f6b9")
		self.assertEqual(pHash,   None)
		self.assertEqual(dHash,   None)
		self.assertEqual(imX,     None)
		self.assertEqual(imY,     None)

	def test_hashImage6(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'lolcat-oregon-trail.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()

		basePath, intName = "LOL", "WAT.jpg"
		fname, hexHash, pHash, dHash, imX, imY = hashFile.hashFile(basePath, intName, fCont, shouldPhash=False)

		self.assertEqual(intName, fname)

		self.assertEqual(hexHash, "7227289a017988b6bdcf61fd4761f6b9")
		self.assertEqual(pHash,   None)
		self.assertEqual(dHash,   None)
		self.assertEqual(imX,     None)
		self.assertEqual(imY,     None)

	def test_hashFile(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		imPath = os.path.join(cwd, 'testimages', 'lolcat-oregon-trail.jpg')

		with open(imPath, "rb") as fp:
			fCont = fp.read()


		hexHash = hashFile.getMd5Hash(fCont)

		self.assertEqual(hexHash, "7227289a017988b6bdcf61fd4761f6b9")



