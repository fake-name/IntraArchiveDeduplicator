
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
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', '83aec17425e9d6720bc27efde7d0f2d0')),
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', '407bc3580af7a999b340145a997e5bc7')),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', '1798dbdf54498f7b6d2e6adc9f00b423')),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', 'a28a0a9253ad1aa2dcbb22309f91721d')),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', 'ed69c0db2493e0eba18d378b22335342')),

	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', '822c823d4e3bd49a35da06a86cb6231e')),
	('lolcat-crocs.png',                 ('c699c3b0df40be264d2566970a01af72', '9e0e86672909bdb35ac06b8730c8512d')),
	('dangerous-to-go-alone.png',        ('351d82c14bbf6c94d97112cd27cc5198', '5217b1c8f8bac745bea087c1c282b9ff')),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', '822c823d4e3bd49a35da06a86cb6231e')),
	('Lolcat_this_is_mah_job_small.png', ('1bb81f4262f6d1219f3d71a5f857cdab', '2ddaf55b1ed59e1b8c0dbd53548808eb')),
	('lolcat-oregon-trail.png',          ('4a282959a53d259283f6e977c9be4143', '2bee65c30033043293a809a4f1439d3f')),
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

		matchsets = []
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

			print("image: {} Hashes: ({} - {}{}), ({} - {}{})".format(
				imName,
				contHexHash, hashes[0], " MISMATCH" if contHexHash != hashes[0] else "",
				pxHexHash, hashes[1], " MISMATCH" if pxHexHash != hashes[1] else ""
				))
			matchsets.append((imName, "input hash",  (contHexHash, hashes[0]))),
			matchsets.append((imName, "resize hash", (pxHexHash, hashes[1]))),
		for imgn, hashtype, hashes in matchsets:

			self.assertEqual(hashes[0], hashes[1],
				"Mismatch in {} of image {} - ({}, {})".format(
					imgn, hashtype, hashes[0], hashes[1]
					))

