
from PIL import Image

import io
import hashlib


import scanner.unitConverters

from PIL import Image
import numpy
import scipy.fftpack

def binary_array_to_hex(arr):
	h = 0
	s = []
	for i,v in enumerate(arr.flatten()):
		if v:
			h += 2**(i % 8)
		if (i % 8) == 7:
			s.append(hex(h)[2:].rjust(2, '0'))
			h = 0
	return "".join(s)



"""
Hash encapsulation. Can be used for dictionary keys and comparisons.
"""
class ImageHash(object):
	def __init__(self, binary_array):
		self.hash = binary_array

	def __str__(self):
		return binary_array_to_hex(self.hash)

	def __repr__(self):
		return repr(self.hash)

	def __sub__(self, other):
		assert self.hash.shape == other.hash.shape, ('ImageHashes must be of the same shape!', self.hash.shape, other.hash.shape)
		return (self.hash != other.hash).sum()

	def __eq__(self, other):
		return numpy.array_equal(self.hash, other.hash)

	def __ne__(self, other):
		return not numpy.array_equal(self.hash, other.hash)

	def __hash__(self):
		return scanner.unitConverters.binary_array_to_int(self.hash)

	def __iter__(self):
		return numpy.nditer(self.hash, order='C')  # Specify memory order, so we're (theoretically) platform agnostic

	def __len__(self):
		return self.hash.size

	def __int__(self):
		ret = 0
		mask = 1 << len(self) - 1
		for bit in numpy.nditer(self.hash, order='C'):  # Specify memory order, so we're (theoretically) platform agnostic
			if bit:
				ret |= mask
			mask >>= 1

		# Convert to signed representation
		VALSIZE = 64
		if ret >= 2**(VALSIZE-1):
			ret = ret - 2**VALSIZE
		return ret





"""
Average Hash computation

Implementation follows http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html

@image must be a PIL instance.
"""
def average_hash(image, hash_size=8):
	image = image.convert("L").resize((hash_size, hash_size), Image.ANTIALIAS)
	pixels = numpy.array(image.getdata()).reshape((hash_size, hash_size))
	avg = pixels.mean()
	diff = pixels > avg
	# make a hash
	return ImageHash(diff), image

"""
Perceptual Hash computation.

Implementation follows http://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html

@image must be a PIL instance.
"""
def phash(image, hash_size=32):
	image = image.convert("L").resize((hash_size, hash_size), Image.ANTIALIAS)
	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((hash_size, hash_size))
	dct = scipy.fftpack.dct(pixels)
	dctlowfreq = dct[:8, 1:9]
	avg = dctlowfreq.mean()
	diff = dctlowfreq > avg
	return ImageHash(diff), image

"""
Difference Hash computation.

following http://www.hackerfactor.com/blog/index.php?/archives/529-Kind-of-Like-That.html

@image must be a PIL instance.
"""
def dhash(image, hash_size=8):
	image = image.convert("L").resize((hash_size + 1, hash_size), Image.ANTIALIAS)
	pixels = numpy.array(image.getdata(), dtype=numpy.float).reshape((hash_size + 1, hash_size))
	# compute differences
	diff = pixels[1:,:] > pixels[:-1,:]
	return ImageHash(diff)



__dir__ = [average_hash, phash, ImageHash]





IMAGE_EXTS = ("bmp", "eps", "gif", "im", "jpeg", "jpg", "msp", "pcx", "png", "ppm", "spider", "tiff", "webp", "xbm")

'''
Generate various hashes of file

basepath/fname are required for determining if the passed file is probably an image (by looking at extensions)
Actual file contents must be in fContents

'''
def hashFile(basePath, fname, fContents, shouldPhash=True):
	# basePath, fname, fContents = arg

	fMD5 = hashlib.md5()
	fMD5.update(fContents)
	hexHash = fMD5.hexdigest()

	pHash = None
	dHash = None

	imX = None
	imY = None

	if (fname.lower().endswith(IMAGE_EXTS) or (basePath.lower().endswith(IMAGE_EXTS) and fname == "")) and shouldPhash:


		im = Image.open(io.BytesIO(fContents))
		pHashArr, im = phash(im)
		dHashArr     = dhash(im)

		pHash = int(pHashArr)
		dHash = int(dHashArr)

		imX, imY = im.size


	return fname, hexHash, pHash, dHash, imX, imY


def getMd5Hash(fContents):
	fMD5 = hashlib.md5()
	fMD5.update(fContents)
	hexHash = fMD5.hexdigest()
	return hexHash

def test():
	import sys
	print(sys.argv)
	if len(sys.argv) < 2:
		print("Need path to image as command line param")
		return
	imPath = sys.argv[1]
	with open(imPath, "rb") as fp:
		cont = fp.read()
		hashes = hashFile(imPath, "", cont)
		print(hashes)


if __name__ == "__main__":
	test()

