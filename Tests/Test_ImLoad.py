
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
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', 'd958d47e04812e34746b9c36f40e0385')),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', 'f238cfe1c2262cc5fea335dc85c3d8ba')),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', '766744a9d5a4c3ae9a14f5b4218bc3af')),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', 'a1a5ca5f755b9a340f52c16a41fddc6d')),
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', '63d4a41d74397ae8b58b70ec880ea66b')),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', '013936aadb798634d26a8d3df4a1d90a')),

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
			image = image.convert("L").resize((HASH_SIZE, HASH_SIZE), Image.NEAREST)
			pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE, HASH_SIZE))

			# Calculate the md5 of the resulting image, to verify the libraries are consistent in their resize behaviour.

			pxStr = str(list(pixels.flatten()))
			fMD5 = hashlib.md5()
			fMD5.update(pxStr.encode("utf-8"))
			pxHexHash = fMD5.hexdigest()

			print("image: {} Hashes: ({} - {}), ({} - {})".format(imName, contHexHash, hashes[0], pxHexHash, hashes[1]))

			self.assertEqual(contHexHash, hashes[0])
			self.assertEqual(pxHexHash, hashes[1])

