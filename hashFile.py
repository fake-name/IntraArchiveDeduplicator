
from PIL import Image

import io
import hashlib




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

# Probably not functional on a 32-bit arch?
def binary_array_to_int(arr):
	tot_sum = 0
	for i,v in enumerate(arr.flatten()):
		if v:
			tot_sum += 1 << i
	return tot_sum

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
		return binary_array_to_int(self.hash)

	def __iter__(self):
		return numpy.nditer(self.hash, order='C')  # Specify memory order, so we're (theoretically) platform agnostic

	# Convert hash to a binary string representation (e.g. literal "10110101..."). Useful for things like database storage, etc...
	def as_binary_string_repr(self):
		return "".join(["1" if val else "0" for val in self ])

def hex_to_hash(hexstr):
	l = []
	if len(hexstr) != 16:
		print(hexstr)
	for i in range(len(hexstr) / 2):
		#for h in hexstr[::2]:
		h = hexstr[i*2:i*2+2]
		v = int("0x" + h, 16)
		for i in range(8):
			l.append(v & 2**i > 0)
	return ImageHash(numpy.array(l))


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


def hashFile(basePath, fname, fContents):
	# basePath, fname, fContents = arg
	fMD5 = hashlib.md5()


	fMD5.update(fContents)
	hexHash = fMD5.hexdigest()
	pHash = None
	dHash = None


	if fname.lower().endswith(IMAGE_EXTS) or (basePath.lower().endswith(IMAGE_EXTS) and fname == ""):


		im = Image.open(io.BytesIO(fContents))
		pHashArr, im = phash(im)
		dHashArr     = dhash(im)
		pHash = "".join(["1" if val else "0" for val in pHashArr ])
		dHash = "".join(["1" if val else "0" for val in dHashArr ])

	return fname, hexHash, pHash, dHash

