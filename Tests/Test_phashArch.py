
import unittest
import scanner.logSetup as logSetup
import os.path
import pArch

# Unit testing driven by lolcat images
# AS GOD INTENDED!

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()

		super().__init__(*args, **kwargs)


	def test_pArch_1(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = os.path.join(cwd, 'testArches', 'testArches.zip')

		arch = pArch.PhashArchive(archPath)


		match = [
			(
				'Lolcat_this_is_mah_job.jpg',
				{
					'hexHash' : 'd9ceeb6b43c2d7d096532eabfa6cf482',
					'type'    : 'image/jpeg',
					'imY'     : 389,
					'pHash'   : -4992890192511777340,
					# 'dHash'   : -4504585791368671746,
					'imX'     : 493
				}
			),
			(
				'Lolcat_this_is_mah_job.png',
				{
					'hexHash' : '1268e704908cc39299d73d6caafc23a0',
					'type'    : 'image/png',
					'imY'     : 389,
					'pHash'   : -4992890192511777340,
					# 'dHash'   : -4504585791368671746,
					'imX'     : 493
				}
			),
			(
				'Lolcat_this_is_mah_job_small.jpg',
				{
					'hexHash' : '40d39c436e14282dcda06e8aff367307',
					'type'    : 'image/jpeg',
					'imY'     : 237,
					'pHash'   : -4992890192511777340,
					# 'dHash'   : -4504585791368671746,
					'imX'     : 300
				}
			),
			(
				'dangerous-to-go-alone.jpg',
				{
					'hexHash' : 'dcd6097eeac911efed3124374f44085b',
					'type'    : 'image/jpeg',
					'imY'     : 307,
					'pHash'   : -7813072021139921681,
					# 'dHash'   : 4576150637722077151,
					'imX'     : 325
				}
			),
			(
				'lolcat-crocs.jpg',
				{
					'hexHash' : '6d0a977694630ac9d1d33a7f068e10f8',
					'type'    : 'image/jpeg',
					'imY'     : 363,
					'pHash'   : -7472365462264617431,
					# 'dHash'   : 167400391896309758,
					'imX'     : 500
				}
			),
			(
				'lolcat-oregon-trail.jpg',
				{
					'hexHash' : '7227289a017988b6bdcf61fd4761f6b9',
					'type'    : 'image/jpeg',
					'imY'     : 356,
					'pHash'   : -3164295607292040329,
					# 'dHash'   : -8660145558008088574,
					'imX'     : 501
				}
			)
		]


		archHashes = list(arch.iterHashes())
		for item in archHashes:
			del item[1]['cont']
		print(archHashes)
		self.assertEqual(archHashes, match)


	def test_pArch_2(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = os.path.join(cwd, 'testArches', 'testArches.zip')

		arch = pArch.PhashArchive(archPath)

		ret = arch.getHashInfo('dangerous-to-go-alone.jpg')
		ret.pop('cont')
		expect = {
			# 'dHash': 4576150637722077151,
			'hexHash': 'dcd6097eeac911efed3124374f44085b',
			'imX': 325,
			'pHash': -7813072021139921681,
			'type': 'image/jpeg',
			'imY': 307
		}

		self.assertEqual(ret, expect)


	def test_pArch_3(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = os.path.join(cwd, 'testArches', 'testArches.7z')

		arch = pArch.PhashArchive(archPath)


		match = [
			('Lolcat_this_is_mah_job.jpg',
				{
					'type': 'image/jpeg',
					'pHash': -4992890192511777340,
					# 'dHash': -4504585791368671746,
					'imY': 389,
					'hexHash': 'd9ceeb6b43c2d7d096532eabfa6cf482',
					'imX': 493
				}
			),
			('Lolcat_this_is_mah_job.png',
				{
					'type': 'image/png',
					'pHash': -4992890192511777340,
					# 'dHash': -4504585791368671746,
					'imY': 389,
					'hexHash': '1268e704908cc39299d73d6caafc23a0',
					'imX': 493
				}
			),
			('Lolcat_this_is_mah_job_small.jpg',
				{
					'type': 'image/jpeg',
					'pHash': -4992890192511777340,
					# 'dHash': -4504585791368671746,
					'imY': 237,
					'hexHash': '40d39c436e14282dcda06e8aff367307',
					'imX': 300
				}
			),
			('dangerous-to-go-alone.jpg',
				{
					'type': 'image/jpeg',
					'pHash': -7813072021139921681,
					# 'dHash': 4576150637722077151,
					'imY': 307,
					'hexHash': 'dcd6097eeac911efed3124374f44085b',
					'imX': 325
				}
			),
			('lolcat-crocs.jpg',
				{
					'type': 'image/jpeg',
					'pHash': -7472365462264617431,
					# 'dHash': 167400391896309758,
					'imY': 363,
					'hexHash': '6d0a977694630ac9d1d33a7f068e10f8',
					'imX': 500
				}
			),
			('lolcat-oregon-trail.jpg',
				{
					'type': 'image/jpeg',
					'pHash': -3164295607292040329,
					# 'dHash': -8660145558008088574,
					'imY': 356,
					'hexHash': '7227289a017988b6bdcf61fd4761f6b9',
					'imX': 501
				}
			)
		]


		archHashes = list(arch.iterHashes())
		for item in archHashes:
			del item[1]['cont']

		print(archHashes)

		self.assertEqual(archHashes, match)


	def test_pArch_4(self):
		cwd = os.path.dirname(os.path.realpath(__file__))
		archPath = os.path.join(cwd, 'testArches', 'testArches.7z')

		arch = pArch.PhashArchive(archPath)

		ret = arch.getHashInfo('dangerous-to-go-alone.jpg')

		# We're not confirming image contents here, so pop that from the list because it's
		# enormous, and I don't want to insert that into the file.
		ret.pop('cont')

		expect = {
			# 'dHash': 4576150637722077151,
			'hexHash': 'dcd6097eeac911efed3124374f44085b',
			'imX': 325,
			'pHash': -7813072021139921681,
			'type': 'image/jpeg',
			'imY': 307
		}

		self.assertEqual(ret, expect)

