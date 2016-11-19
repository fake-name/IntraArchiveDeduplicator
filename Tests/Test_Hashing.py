
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
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', 'c353223412ff3baccca3826416addd9e'), 'FFFTTTTTTFFFTTTTTTFFFFFFFFTFFFFTFTTTFFFFTFFTTFFFFFFTTTFFFFTFTFFF',
		[0.0, 3.0, 5.0, 0.0, 5.0, 0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 42.0, 25.0, 19.0, 129.0, 152.0, 19.0, 0.0, 0.0, 0.0, 60.0, 76.0, 151.0, 217.0, 200.0, 145.0, 0.0, 0.0,
			2.0, 71.0, 96.0, 49.0, 128.0, 118.0, 4.0, 0.0, 0.0, 0.0, 17.0, 72.0, 100.0, 133.0, 142.0, 82.0, 0.0, 0.0, 0.0, 5.0, 158.0, 91.0, 87.0, 120.0, 52.0, 0.0, 0.0,
			1.0, 3.0, 11.0, 72.0, 133.0, 88.0, 87.0, 0.0, 0.0, 0.0, 0.0, 247.0, 1.0, 255.0, 7.0, 0.0, 0.0]),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', 'a4ad804d417400f8129e9c59117e1b64'), 'TTTFFFFFFTFTTTFFFFTTTTTTFFFTTTFFTTFFFTFTTFTTTFTTTTFFFTFTTFTTTTTT',
		[216.0, 217.0, 221.0, 220.0, 221.0, 225.0, 226.0, 227.0, 227.0, 222.0, 223.0, 76.0, 61.0, 29.0, 217.0, 227.0, 226.0, 230.0, 222.0, 111.0, 137.0, 127.0, 83.0,
			102.0, 111.0, 227.0, 228.0, 224.0, 152.0, 144.0, 174.0, 161.0, 103.0, 76.0, 218.0, 230.0, 181.0, 159.0, 145.0, 143.0, 109.0, 140.0, 130.0, 108.0, 162.0, 164.0,
			103.0, 168.0, 115.0, 110.0, 162.0, 173.0, 168.0, 59.0, 184.0, 182.0, 187.0, 135.0, 49.0, 168.0, 154.0, 169.0, 171.0, 186.0, 255.0, 4.0, 187.0, 255.0, 253.0, 254.0, 190.0, 255.0]),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', '03a22f7c50628f76013ee462802f0b8a'), 'TTTFFFFFFTFTTTFFFFTTTTTTFFFTTTFFTTFFFTFTTFTTTFTTTTFFFTFTTFTTTTTT',
		[216.0, 217.0, 221.0, 220.0, 221.0, 225.0, 226.0, 227.0, 227.0, 222.0, 223.0, 77.0, 61.0, 28.0, 217.0, 227.0, 226.0, 230.0, 222.0, 111.0, 137.0, 127.0, 83.0,
			102.0, 111.0, 227.0, 228.0, 224.0, 152.0, 144.0, 174.0, 161.0, 103.0, 76.0, 218.0, 230.0, 181.0, 159.0, 145.0, 143.0, 109.0, 140.0, 130.0, 107.0, 162.0, 164.0,
			103.0, 168.0, 115.0, 110.0, 162.0, 173.0, 167.0, 59.0, 184.0, 182.0, 187.0, 135.0, 49.0, 168.0, 154.0, 168.0, 171.0, 186.0, 255.0, 4.0, 186.0, 255.0, 253.0, 254.0, 190.0, 255.0] ),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', 'cc8ebadcd54106f1de68c1c79aa140cc'), 'TTTFFFFFFTFTTTFFFFTTTTTTFFFTTTFFTTFFFFFTTFTTFFTTTFFTFTFTTFTTTTTT',
		[216.0, 219.0, 220.0, 219.0, 222.0, 225.0, 225.0, 226.0, 228.0, 221.0, 225.0, 82.0, 59.0, 49.0, 211.0, 226.0, 228.0, 230.0, 223.0, 112.0, 133.0, 112.0, 78.0,
			76.0, 114.0, 226.0, 229.0, 224.0, 157.0, 145.0, 160.0, 166.0, 103.0, 83.0, 220.0, 229.0, 171.0, 173.0, 146.0, 151.0, 112.0, 142.0, 130.0, 128.0, 164.0, 164.0,
			134.0, 170.0, 156.0, 118.0, 162.0, 172.0, 163.0, 74.0, 177.0, 174.0, 176.0, 100.0, 54.0, 173.0, 153.0, 174.0, 165.0, 195.0, 252.0, 30.0, 204.0, 250.0, 241.0, 249.0, 214.0, 253.0] ),
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', '0d51926435b5e33c0f96fc703b46e3c7'), 'TFTFFFTTTTFTTFTTFFFFFFFTTTTTTTTFTTFFTFFTFFTTTTTTTTTFTTTFFTFFFTTT',
		[67.0, 134.0, 33.0, 128.0, 101.0, 180.0, 105.0, 102.0, 92.0, 59.0, 86.0, 74.0, 75.0, 156.0, 170.0, 111.0, 105.0, 98.0, 86.0, 94.0, 83.0, 92.0, 183.0, 130.0,
			89.0, 77.0, 62.0, 75.0, 65.0, 83.0, 95.0, 189.0, 124.0, 90.0, 89.0, 92.0, 67.0, 108.0, 105.0, 64.0, 142.0, 119.0, 88.0, 68.0, 97.0, 91.0, 65.0, 65.0, 94.0, 70.0,
			122.0, 143.0, 116.0, 105.0, 101.0, 101.0, 116.0, 78.0, 141.0, 139.0, 151.0, 127.0, 119.0, 57.0, 60.0, 135.0, 119.0, 84.0, 145.0, 140.0, 150.0, 122.0]),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', 'df3fd8283386a789d9499f6a7a4761f8'), 'TFFFFTTTTFFFFFFFTTTTTFFTFTTTTTTTFFTTFTTTTTFFFFFFTFFTTFFFTFTTTFFF',
		[8.0, 19.0, 19.0, 16.0, 44.0, 49.0, 16.0, 17.0, 21.0, 9.0, 10.0, 9.0, 14.0, 186.0, 203.0, 139.0, 83.0, 5.0, 2.0, 2.0, 0.0, 7.0, 199.0, 49.0, 181.0, 102.0,
			127.0, 17.0, 3.0, 0.0, 11.0, 95.0, 115.0, 186.0, 145.0, 157.0, 174.0, 217.0, 180.0, 169.0, 82.0, 40.0, 240.0, 177.0, 129.0, 254.0, 255.0, 187.0, 171.0, 173.0,
			114.0, 46.0, 33.0, 23.0, 242.0, 137.0, 177.0, 86.0, 47.0, 116.0, 39.0, 8.0, 126.0, 71.0, 183.0, 0.0, 83.0, 241.0, 63.0, 0.0, 0.0, 3.0]),
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


		for imName, hashes, dhash, expect_pixels in files:


			imPath = os.path.join(cwd, 'testimages', imName)

			with open(imPath, "rb") as fp:
				fCont = fp.read()

			fMD5 = hashlib.md5()
			fMD5.update(fCont)
			contHexHash = fMD5.hexdigest()



			image = Image.open(io.BytesIO(fCont))
			image = image.convert("L").resize((HASH_SIZE+1, HASH_SIZE), Image.NEAREST)
			pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((HASH_SIZE+1, HASH_SIZE))


			pixList = list(pixels.flatten())
			pxStr = str(pixList)
			fMD5 = hashlib.md5()
			fMD5.update(pxStr.encode("utf-8"))
			pxHexHash = fMD5.hexdigest()

			self.assertEqual(contHexHash, hashes[0])
			print(imName, pixList, pxHexHash, hashes[1])
			self.assertEqual(expect_pixels, pixList)
			self.assertEqual(pxHexHash, hashes[1])



			diff = pixels[1:,:] > pixels[:-1,:]
			diff = diff.flatten()
			diff = ['T' if val else 'F' for val in diff ]
			self.assertEqual(dhash, "".join(diff))


if __name__ == '__main__':
	unittest.main()
