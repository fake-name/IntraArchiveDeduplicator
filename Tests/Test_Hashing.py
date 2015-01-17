
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
	('dangerous-to-go-alone.jpg',        ('dcd6097eeac911efed3124374f44085b', '98f1be588e20cc368b5f611befee8ddf'), 'FFTTTTTTTFFFFFFTTTFFFFFFTTFFFFTFFTTTFFFFFFFTTFTFFFFFFTTTTTFTTTTT',
		[0.0, 22.0, 17.0, 20.0, 6.0, 26.0, 88.0, 12.0, 0.0, 0.0, 19.0, 53.0, 90.0, 121.0, 190.0, 167.0,
			13.0, 0.0, 0.0, 18.0, 76.0, 92.0, 147.0, 180.0, 142.0, 6.0, 0.0, 0.0, 14.0, 81.0, 83.0, 111.0,
			151.0, 85.0, 0.0, 0.0, 1.0, 1.0, 93.0, 105.0, 94.0, 124.0, 100.0, 39.0, 0.0, 1.0, 3.0, 64.0, 73.0,
			107.0, 83.0, 80.0, 30.0, 0.0, 15.0, 17.0, 46.0, 33.0, 79.0, 59.0, 26.0, 16.0, 17.0, 29.0, 58.0,
			84.0, 57.0, 74.0, 67.0, 43.0, 65.0, 34.0]),
	('Lolcat_this_is_mah_job.jpg',       ('d9ceeb6b43c2d7d096532eabfa6cf482', 'bfdecd591bdb8ca59d235a735bd16023'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF',
		[224.0, 213.0, 140.0, 122.0, 192.0, 237.0, 227.0, 226.0, 229.0, 220.0, 132.0, 77.0, 58.0, 55.0,
			153.0, 229.0, 227.0, 229.0, 183.0, 124.0, 137.0, 127.0, 97.0, 45.0, 144.0, 238.0, 233.0, 152.0,
			148.0, 145.0, 144.0, 135.0, 109.0, 112.0, 159.0, 196.0, 132.0, 149.0, 157.0, 132.0, 137.0, 160.0,
			151.0, 97.0, 159.0, 151.0, 144.0, 174.0, 129.0, 135.0, 174.0, 172.0, 95.0, 138.0, 181.0, 172.0, 172.0,
			163.0, 169.0, 171.0, 170.0, 170.0, 178.0, 194.0, 175.0, 175.0, 182.0, 186.0, 182.0, 184.0, 182.0, 190.0]),
	('Lolcat_this_is_mah_job.png',       ('1268e704908cc39299d73d6caafc23a0', 'bfdecd591bdb8ca59d235a735bd16023'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF',
		[224.0, 213.0, 140.0, 122.0, 192.0, 237.0, 227.0, 226.0, 229.0, 220.0, 132.0, 77.0, 58.0, 55.0,
			153.0, 229.0, 227.0, 229.0, 183.0, 124.0, 137.0, 127.0, 97.0, 45.0, 144.0, 238.0, 233.0, 152.0,
			148.0, 145.0, 144.0, 135.0, 109.0, 112.0, 159.0, 196.0, 132.0, 149.0, 157.0, 132.0, 137.0, 160.0,
			151.0, 97.0, 159.0, 151.0, 144.0, 174.0, 129.0, 135.0, 174.0, 172.0, 95.0, 138.0, 181.0, 172.0, 172.0,
			163.0, 169.0, 171.0, 170.0, 170.0, 178.0, 194.0, 175.0, 175.0, 182.0, 186.0, 182.0, 184.0, 182.0, 190.0]),
	('Lolcat_this_is_mah_job_small.jpg', ('40d39c436e14282dcda06e8aff367307', '4cf880c12d01ab363393c5292b89afb0'), 'TTFFFFFTFTTTTTFFFTTTTTTTFFFTFTTFTTFFTTFTFFTTFFTFTTFFTTFTTTTTTTTF',
		[224.0, 213.0, 140.0, 122.0, 193.0, 236.0, 226.0, 226.0, 229.0, 220.0, 132.0, 77.0, 58.0, 55.0,
			153.0, 228.0, 227.0, 229.0, 183.0, 124.0, 137.0, 128.0, 96.0, 45.0, 144.0, 238.0, 232.0, 152.0,
			147.0, 145.0, 144.0, 135.0, 109.0, 112.0, 158.0, 195.0, 132.0, 149.0, 156.0, 132.0, 137.0, 160.0,
			151.0, 98.0, 159.0, 151.0, 145.0, 174.0, 129.0, 135.0, 174.0, 172.0, 95.0, 138.0, 181.0, 172.0, 173.0,
			163.0, 168.0, 171.0, 170.0, 170.0, 178.0, 193.0, 175.0, 175.0, 181.0, 185.0, 181.0, 184.0, 182.0, 189.0]),
	('lolcat-crocs.jpg',                 ('6d0a977694630ac9d1d33a7f068e10f8', 'ba44fac3748cdb48d952a8e6abeda013'), 'FFFFFFTFFTFTFFTFTFTTTFFTTTFFFTFFTTTTTTTFFFTTTTFTTFFTTTTTTTTTTTTF',
		[135.0, 115.0, 122.0, 142.0, 164.0, 150.0, 106.0, 106.0, 88.0, 80.0, 82.0, 81.0, 115.0, 145.0,
			128.0, 101.0, 85.0, 101.0, 73.0, 83.0, 90.0, 142.0, 159.0, 95.0, 89.0, 77.0, 89.0, 85.0, 95.0,
			87.0, 142.0, 160.0, 104.0, 86.0, 83.0, 71.0, 83.0, 91.0, 76.0, 82.0, 130.0, 110.0, 106.0, 102.0,
			96.0, 97.0, 100.0, 67.0, 75.0, 79.0, 125.0, 146.0, 122.0, 104.0, 96.0, 110.0, 97.0, 74.0, 109.0,
			154.0, 139.0, 121.0, 105.0, 130.0, 124.0, 141.0, 144.0, 158.0, 162.0, 159.0, 155.0, 125.0]),
	('lolcat-oregon-trail.jpg',          ('7227289a017988b6bdcf61fd4761f6b9', 'b329b35a7e416da5969fe802533712e4'), 'TFFFFTTTTTFFFFFFTTTTTFTTFTTTTTTTTFFTFTTTTTFFFFFFFFTTTFFFFFFFFFTF',
		[13.0, 14.0, 14.0, 37.0, 129.0, 84.0, 26.0, 25.0, 20.0, 10.0, 13.0, 3.0, 74.0, 118.0, 104.0,
			147.0, 89.0, 29.0, 4.0, 2.0, 0.0, 84.0, 67.0, 79.0, 182.0, 144.0, 56.0, 45.0, 75.0, 40.0, 148.0,
			99.0, 133.0, 199.0, 159.0, 79.0, 205.0, 212.0, 153.0, 165.0, 143.0, 114.0, 132.0, 101.0, 43.0,
			241.0, 245.0, 177.0, 146.0, 152.0, 78.0, 48.0, 31.0, 59.0, 163.0, 161.0, 95.0, 99.0, 105.0, 69.0,
			72.0, 42.0, 34.0, 121.0, 71.0, 27.0, 42.0, 52.0, 51.0, 33.0, 50.0, 48.0]),
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

			imTmp = Image.open(io.BytesIO(fCont))
			imTmp = imTmp.convert("L")
			imTmp = imTmp.resize((HASH_SIZE + 1, HASH_SIZE), Image.ANTIALIAS)
			imDatTmp = imTmp.getdata()
			arTmp = numpy.array(imDatTmp, dtype=numpy.float)



			image = Image.open(io.BytesIO(fCont))
			image = image.convert("L")
			image = image.resize((HASH_SIZE + 1, HASH_SIZE), Image.ANTIALIAS)
			imDat = image.getdata()
			pixels = numpy.array(imDat, dtype=numpy.float)
			pixels = pixels.reshape((HASH_SIZE + 1, HASH_SIZE))

			pixList = list(pixels.flatten())
			pxStr = str(pixList)

			fMD5 = hashlib.md5()
			fMD5.update(pxStr.encode("utf-8"))
			pxHexHash = fMD5.hexdigest()


			self.assertEqual(contHexHash, hashes[0])
			self.assertEqual(expect_pixels, pixList)
			self.assertEqual(pxHexHash, hashes[1])

			diff = pixels[1:,:] > pixels[:-1,:]
			diff = diff.flatten()
			diff = ['T' if val else 'F' for val in diff ]
			self.assertEqual(dhash, "".join(diff))


if __name__ == '__main__':
	unittest.main()
