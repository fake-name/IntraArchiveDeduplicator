
import unittest

from PIL import Image
import numpy
import scipy.fftpack
import os.path
import io
import hashlib

expect_4 = [ 2.0,
			 1.8477590650225735,
			 1.4142135623730951,
			 0.76536686473017967,
			 2.0,
			 0.76536686473017967,
			-1.4142135623730951,
			-1.8477590650225735,
			 2.0,
			-0.76536686473017967,
			-1.4142135623730951,
			 1.8477590650225735,
			 2.0,
			-1.8477590650225735,
			 1.4142135623730951,
			-0.76536686473017967
			]

expect_5 = [ 2.0,
			 1.9021130325903073,
			 1.6180339887498949,
			 1.1755705045849463,
			 0.61803398874989501,
			 2.0,
			 1.1755705045849465,
			-0.6180339887498949,
			-1.9021130325903073,
			-1.6180339887498947,
			 2.0,
			 2.2204460492503131e-16,
			-2.0,
			 0.0,
			 2.0,
			 2.0,
			-1.1755705045849463,
			-0.61803398874989468,
			 1.9021130325903075,
			-1.6180339887498949,
			 2.0,
			-1.9021130325903071,
			 1.6180339887498949,
			-1.1755705045849463,
			 0.61803398874989468
			 ]

expect_6 = [ 2.0,
			 1.9318516525781368,
			 1.7320508075688774,
			 1.4142135623730951,
			 1.0000000000000002,
			 0.51763809020504203,
			 2.0,
			 1.4142135623730954,
			 0.0,
			-1.4142135623730951,
			-2.0,
			-1.4142135623730954,
			 2.0,
			 0.51763809020504126,
			-1.7320508075688776,
			-1.4142135623730954,
			 1.0,
			 1.9318516525781366,
			 2.0,
			-0.51763809020504126,
			-1.7320508075688776,
			 1.4142135623730954,
			 1.0,
			-1.9318516525781366,
			 2.0,
			-1.4142135623730954,
			 0.0,
			 1.4142135623730951,
			-2.0,
			 1.4142135623730954,
			 2.0,
			-1.9318516525781368,
			 1.7320508075688774,
			-1.4142135623730951,
			 1.0000000000000002,
			-0.51763809020504203
			]


files = [
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', '98f1be588e20cc368b5f611befee8ddf'), 'FFTTTTTTTFFFFFFTTTFFFFFFTTFFFFTFFTTTFFFFFFFTTFTFFFFFFTTTTTFTTTTT'),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', 'bfdecd591bdb8ca59d235a735bd16023'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF'),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', 'bfdecd591bdb8ca59d235a735bd16023'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF'),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', '4cf880c12d01ab363393c5292b89afb0'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF'),
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', 'ba44fac3748cdb48d952a8e6abeda013'), 'FFFFFFTFFTFTFFTFTFTTTFFTTTFFFTFFTTTTTTTFFFTTTTFTTFFTTTTTTTTTTTTF'),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', 'b329b35a7e416da5969fe802533712e4'), 'TFFFFTTTTTFFFFFFTTTTTFTTFTTTTTTTTFFTFTTTTTFFFFFFFFTTTFFFFFFFFFTF'),

]

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setUp(self):
		pass


	def test_DCT_size_4(self):
		hash_size = 4
		pixels = numpy.identity(hash_size, dtype=numpy.float)
		dct = scipy.fftpack.dct(pixels)
		dct = list(dct.flatten())
		self.assertEqual(expect_4, dct)

	def test_DCT_size_5(self):
		hash_size = 5
		pixels = numpy.identity(hash_size, dtype=numpy.float)
		dct = scipy.fftpack.dct(pixels)
		dct = list(dct.flatten())
		self.assertEqual(expect_5, dct)

	def test_DCT_size_6(self):
		hash_size = 6
		pixels = numpy.identity(hash_size, dtype=numpy.float)
		dct = scipy.fftpack.dct(pixels)
		dct = list(dct.flatten())
		self.assertEqual(expect_6, dct)



	def test_hashImage1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))

		HASH_SIZE = 8

		for imName, hashes, dhash in files:


			imPath = os.path.join(cwd, 'testimages', imName)

			with open(imPath, "rb") as fp:
				fCont = fp.read()

			fMD5 = hashlib.md5()
			fMD5.update(fCont)
			contHexHash = fMD5.hexdigest()

			image = Image.open(io.BytesIO(fCont))
			image = image.convert("L").resize((HASH_SIZE + 1, HASH_SIZE), Image.ANTIALIAS)
			pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE + 1, HASH_SIZE))

			pxStr = str(list(pixels.flatten()))
			fMD5 = hashlib.md5()
			fMD5.update(pxStr.encode("utf-8"))
			pxHexHash = fMD5.hexdigest()


			self.assertEqual(contHexHash, hashes[0])
			self.assertEqual(pxHexHash, hashes[1])

			diff = pixels[1:,:] > pixels[:-1,:]
			diff = diff.flatten()
			diff = ['T' if val else 'F' for val in diff ]
			self.assertEqual(dhash, "".join(diff))



if __name__ == '__main__':
	unittest.main()