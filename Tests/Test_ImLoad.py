
import unittest

import os.path
from PIL import Image
import io
import numpy
import hashlib

# Unit testing driven by lolcat images
# AS GOD INTENDED!

HASH_SIZE = 32

files = [
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', '64d3b5f0b78c5f6f2627c6cbd6e81395')),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', 'd723ffdf08d4dc6627131285e9b4ee6e')),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', 'd723ffdf08d4dc6627131285e9b4ee6e')),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', '778047a142172fc21e3945c1f3f74c0d')),
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', 'cccf788f61adc6c451993e0124464032')),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', '8166ee6ddaa5a874506cfbe598d322c8')),

]


# Verify the loading process for images is consistent.
# Probably unnecessary, but written in the process of
# trying to track down why some unit-tests related to
# image hashing were failing in a VM, and not natively.

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)


	def test_hashImage1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))


		for imName, hashes in files:


			imPath = os.path.join(cwd, 'testimages', imName)

			with open(imPath, "rb") as fp:
				fCont = fp.read()

			fMD5 = hashlib.md5()
			fMD5.update(fCont)
			contHexHash = fMD5.hexdigest()

			image = Image.open(io.BytesIO(fCont))
			image = image.convert("L").resize((HASH_SIZE, HASH_SIZE), Image.ANTIALIAS)
			pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE, HASH_SIZE))

			pxStr = str(list(pixels.flatten()))
			fMD5 = hashlib.md5()
			fMD5.update(pxStr.encode("utf-8"))
			pxHexHash = fMD5.hexdigest()


			self.assertEqual(contHexHash, hashes[0])
			self.assertEqual(pxHexHash, hashes[1])

