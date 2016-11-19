
import unittest
import scanner.logSetup as logSetup
import os.path
import pArch

# Unit testing driven by lolcat images
# AS GOD INTENDED!

arches = [
		"allArch.zip",
		"notQuiteAllArch.zip",
		"regular.zip",
		"small.zip",
		"testArch.zip",
		"z_reg_junk.zip",
		"z_reg.zip",
		"z_sml_u.zip",
		"z_sml_w.zip",
		"z_sml.zip",
]

expect = {
	'z_sml.zip':
		[
			(
				'129165237051396578(s).jpg',
				{
					'imY': 373,
					'hexHash': '7c257ec7fdfd24f249d290dc47dcc71c',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 249,
					# 'dHash': 4593710720834346496,
					'pHash': -5788352938335285257
				}
			),
			(
				'test.txt',
				{
					'imY': None,
					'hexHash': 'b3a79c95a10b4cc0a838b35782b4dc0a',
					'type': 'ASCII text, with CRLF line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			)
		],
	'testArch.zip':
		[
			(
				'Lolcat_this_is_mah_job.png',
				{
					'imY': 389,
					'hexHash': '1268e704908cc39299d73d6caafc23a0',
					'type': 'PNG image data, 493 x 389, 8-bit/color RGB, non-interlaced',
					'imX': 493,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'Lolcat_this_is_mah_job_small.jpg',
				{
					'imY': 237,
					'hexHash': '40d39c436e14282dcda06e8aff367307',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 300,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'dangerous-to-go-alone.jpg',
				{
					'imY': 307,
					'hexHash': 'dcd6097eeac911efed3124374f44085b',
					'type': 'JPEG image data, JFIF standard 1.02',
					'imX': 325,
					# 'dHash': 4576150637722077151,
					'pHash': -149413575039568585
				}
			)
		],
	'z_reg.zip':
		[
			(
				'129165237051396578.jpg',
				{
					'imY': 497,
					'hexHash': 'b688e3ead00ca1453f860b408c446ec2',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 332,
					# 'dHash': 4593710720968564225,
					'pHash': -5788352938335285257
				}
			),
			(
				'test.txt',
				{
					'imY': None,
					'hexHash': 'b3a79c95a10b4cc0a838b35782b4dc0a',
					'type': 'ASCII text, with CRLF line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			)
		],
	'z_reg_junk.zip':
		[
			(
				'129165237051396578.jpg',
				{
					'imY': 497,
					'hexHash': 'b688e3ead00ca1453f860b408c446ec2',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 332,
					# 'dHash': 4593710720968564225,
					'pHash': -5788352938335285257
				}
			),
			(
				'Thumbs.db',
				{
					'imY': None,
					'hexHash': '2ea0b76437adb1dfb8889beab9d7ef3b',
					'type': 'Composite Document File V2 Document, No summary info',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			),
			(
				'__MACOSX/test.txt',
				{
					'imY': None,
					'hexHash': '1ad84adee17e7d3525528ff7e381a900',
					'type': 'ASCII text, with no line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			),
			(
				'deleted.txt',
				{
					'imY': None,
					'hexHash': '2fe06876bc7694a6357e5d9c5f05e0ab',
					'type': 'ASCII text, with no line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			),
			(
				'test.txt',
				{
					'imY': None,
					'hexHash': 'b3a79c95a10b4cc0a838b35782b4dc0a',
					'type': 'ASCII text, with CRLF line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			)
		],
	'regular.zip':
		[
			(
				'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',
				{
					'imY': 375,
					'hexHash': '35484890b48148d260b52ebbb7493ffc',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 500,
					# 'dHash': 5546533486212567551,
					'pHash': -4230769653536099758
				}
			),
			(
				'funny-pictures-cat-looks-like-an-owl.jpg',
				{
					'imY': 442,
					'hexHash': 'bd914f72d824d2a18d076f7643017505',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 492,
					# 'dHash': -4629305759067799552,
					'pHash': -93277392328150
				}
			),
			(
				'funny-pictures-cat-will-do-science.jpg',
				{
					'imY': 674,
					'hexHash': '5b5620b0cfcb469aef632864707a0445',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 500,
					# 'dHash': 1119025673978783491,
					'pHash': -5208810276318177639
				}
			),
			(
				'funny-pictures-kitten-rules-a-tower.jpg',
				{
					'imY': 375,
					'hexHash': 'a26d63bdbb38621b8f44c563ff496987',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 500,
					# 'dHash': 9187567978625498130,
					'pHash': -5860684349360469885
				}
			)
		],
	'z_sml_w.zip':
		[
			(
				'129165237051396578(s).jpg',
				{
					'imY': 100,
					'hexHash': 'e8566233d43b2e964b77471a99c5fa36',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 100,
					# 'dHash': 0,
					'pHash': 0}
				)
		,
			(
				'test.txt',
				{
					'imY': None,
					'hexHash': 'b3a79c95a10b4cc0a838b35782b4dc0a',
					'type': 'ASCII text, with CRLF line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			)
		],
	'z_sml_u.zip':
		[
			(
				'129165237051396578(s).jpg',
				{
					'imY': 373,
					'hexHash': '7c257ec7fdfd24f249d290dc47dcc71c',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 249,
					# 'dHash': 4593710720834346496,
					'pHash': -5788352938335285257
				}
			),
			(
				'test.txt',
				{
					'imY': None,
					'hexHash': '1234ae2e7a21c94100cb60773efe482b',
					'type': 'ASCII text, with CRLF line terminators',
					'imX': None,
					# 'dHash': None,
					'pHash': None
				}
			)
		],
	'allArch.zip':
		[
			(
				'Lolcat_this_is_mah_job.jpg',
				{
					'imY': 389,
					'hexHash': 'd9ceeb6b43c2d7d096532eabfa6cf482',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 493,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'Lolcat_this_is_mah_job.png',
				{
					'imY': 389,
					'hexHash': '1268e704908cc39299d73d6caafc23a0',
					'type': 'PNG image data, 493 x 389, 8-bit/color RGB, non-interlaced',
					'imX': 493,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'Lolcat_this_is_mah_job_small.jpg',
				{
					'imY': 237,
					'hexHash': '40d39c436e14282dcda06e8aff367307',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 300,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'dangerous-to-go-alone.jpg',
				{
					'imY': 307,
					'hexHash': 'dcd6097eeac911efed3124374f44085b',
					'type': 'JPEG image data, JFIF standard 1.02',
					'imX': 325,
					# 'dHash': 4576150637722077151,
					'pHash': -149413575039568585
				}
			),
			(
				'lolcat-crocs.jpg',
				{
					'imY': 363,
					'hexHash': '6d0a977694630ac9d1d33a7f068e10f8',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 500,
					# 'dHash': 167400391896309758,
					'pHash': -5569898607211671279
				}
			),
			(
				'lolcat-oregon-trail.jpg',
				{
					'imY': 356,
					'hexHash': '7227289a017988b6bdcf61fd4761f6b9',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 501,
					# 'dHash': -8660145558008088574,
					'pHash': -4955310669995365332
				}
			)
		],
	'notQuiteAllArch.zip':
		[
			(
				'Lolcat_this_is_mah_job.jpg',
				{
					'imY': 389,
					'hexHash': 'd9ceeb6b43c2d7d096532eabfa6cf482',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 493,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'Lolcat_this_is_mah_job.png',
				{
					'imY': 389,
					'hexHash': '1268e704908cc39299d73d6caafc23a0',
					'type': 'PNG image data, 493 x 389, 8-bit/color RGB, non-interlaced',
					'imX': 493,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'Lolcat_this_is_mah_job_small.jpg',
				{
					'imY': 237,
					'hexHash': '40d39c436e14282dcda06e8aff367307',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 300,
					# 'dHash': -4504585791368671746,
					'pHash': 27427800275512429
				}
			),
			(
				'lolcat-crocs.jpg',
				{
					'imY': 363,
					'hexHash': '6d0a977694630ac9d1d33a7f068e10f8',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 500,
					# 'dHash': 167400391896309758,
					'pHash': -5569898607211671279
				}
			),
			(
				'lolcat-oregon-trail.jpg',
				{
					'imY': 356,
					'hexHash': '7227289a017988b6bdcf61fd4761f6b9',
					'type': 'JPEG image data, JFIF standard 1.01',
					'imX': 501,
					# 'dHash': -8660145558008088574,
					'pHash': -4955310669995365332
				}
			)
		],
	'small.zip':
		[
			(
				'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png',
				{
					'imY': 281,
					'hexHash': 'b4c3d02411a34e1222972cc262a40b89',
					'type': 'PNG image data, 375 x 281, 8-bit/color RGB, non-interlaced',
					'imX': 375,
					# 'dHash': 5546533486212567551,
					'pHash': -4230769653536099758
				}
			),
			(
				'funny-pictures-cat-looks-like-an-owl-ps.png',
				{
					'imY': 332,
					'hexHash': '740555f4e730ab2c6c261be7d53a3156',
					'type': 'PNG image data, 369 x 332, 8-bit/color RGB, non-interlaced',
					'imX': 369,
					# 'dHash': -4629305759067799552,
					'pHash': -93277392328150
				}
			),
			(
				'funny-pictures-cat-will-do-science-ps.png',
				{
					'imY': 506,
					'hexHash': 'c47ed1cd79c4e7925b8015cb51bbab10',
					'type': 'PNG image data, 375 x 506, 8-bit/color RGB, non-interlaced',
					'imX': 375,
					# 'dHash': 1119025673978783491,
					'pHash': -6361731780925024615
				}
			),
			(
				'funny-pictures-kitten-rules-a-tower-ps.png',
				{
					'imY': 281,
					'hexHash': 'fb64248009dde8605a95b041b772544a',
					'type': 'PNG image data, 375 x 281, 8-bit/color RGB, non-interlaced',
					'imX': 375,
					# 'dHash': 9187567978625498130,
					'pHash': -5860684349360469885
				}
			)
		]
	}


class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		logSetup.initLogging()

		super().__init__(*args, **kwargs)


	def test_validate_arches(self):

		got = {}
		for arch_name in arches:
			cwd = os.path.dirname(os.path.realpath(__file__))
			archPath = os.path.join(cwd, 'test_ptree_base', arch_name)

			arch = pArch.PhashArchive(archPath)


			archHashes = list(arch.iterHashes())
			for item in archHashes:
				del item[1]['cont']
			got[arch_name] = archHashes

		expect_keys = list(expect.keys())
		got_keys    = list(got.keys())

		expect_keys.sort()
		got_keys.sort()

		self.assertEqual(len(expect), len(got))
		self.assertEqual(expect_keys, got_keys)

		for key in expect_keys:
			self.assertEqual(expect[key], got[key])


