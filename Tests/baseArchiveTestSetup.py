
'''
This file contains what the DB should contain after all the files in the test_ptree directory are hashed.

All test images are lolcats. AS GOD INTENDED.

'''

import os
import os.path
import tempfile

TEST_ZIP_PATH = tempfile.mkdtemp()

def insertCwd(inStr):
	cwd = os.path.dirname(os.path.realpath(__file__))
	inStr = inStr.format(cwd=cwd)
	return inStr

CONTENTS = [

        [1, '{cwd}/test_ptree/allArch.zip',                         '',                                                                   '9d7d02a6bff693737904c5d1a35c89cc', None, None, None, None],
        [2, '{cwd}/test_ptree/allArch.zip',                         'Lolcat_this_is_mah_job.jpg',                                         'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429, None, 493, 389],
        [3, '{cwd}/test_ptree/allArch.zip',                         'Lolcat_this_is_mah_job.png',                                         '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389],
        [4, '{cwd}/test_ptree/allArch.zip',                         'Lolcat_this_is_mah_job_small.jpg',                                   '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237],
        [5, '{cwd}/test_ptree/allArch.zip',                         'dangerous-to-go-alone.jpg',                                          'dcd6097eeac911efed3124374f44085b', -149413575039568585, None, 325, 307],
        [6, '{cwd}/test_ptree/allArch.zip',                         'lolcat-crocs.jpg',                                                   '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500, 363],
        [7, '{cwd}/test_ptree/allArch.zip',                         'lolcat-oregon-trail.jpg',                                            '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501, 356],
        [8, '{cwd}/test_ptree/notQuiteAllArch.zip',                 '',                                                                   'd3c2108bfc69602cfbf2f821eb874ccd', None, None, None, None],
        [9, '{cwd}/test_ptree/notQuiteAllArch.zip',                 'Lolcat_this_is_mah_job.jpg',                                         'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429, None, 493, 389],
        [10, '{cwd}/test_ptree/notQuiteAllArch.zip',                'Lolcat_this_is_mah_job.png',                                         '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389],
        [11, '{cwd}/test_ptree/notQuiteAllArch.zip',                'Lolcat_this_is_mah_job_small.jpg',                                   '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237],
        [12, '{cwd}/test_ptree/notQuiteAllArch.zip',                'lolcat-crocs.jpg',                                                   '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500, 363],
        [13, '{cwd}/test_ptree/notQuiteAllArch.zip',                'lolcat-oregon-trail.jpg',                                            '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501, 356],
        [14, '{cwd}/test_ptree/regular-u.zip',                      '',                                                                   '5078998b7b0ccda8937d96b2e20fe0f4', None, None, None, None],
        [15, '{cwd}/test_ptree/regular-u.zip',                      'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',                           '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500, 375],
        [16, '{cwd}/test_ptree/regular-u.zip',                      'funny-pictures-cat-looks-like-an-owl.jpg',                           'bd914f72d824d2a18d076f7643017505', -93277392328150, None, 492, 442],
        [17, '{cwd}/test_ptree/regular-u.zip',                      'funny-pictures-cat-will-do-science.jpg',                             '5b5620b0cfcb469aef632864707a0445', -5208810276318177639, None, 500, 674],
        [18, '{cwd}/test_ptree/regular-u.zip',                      'funny-pictures-kitten-rules-a-tower.jpg',                            'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500, 375],
        [19, '{cwd}/test_ptree/regular-u.zip',                      'superheroes-batman-superman-i-would-watch-the-hell-out-of-this.jpg', '2931dfcefe6af7c5d024eb798ac5e7c6', -8034280126218048380, None, 472, 700],
        [20, '{cwd}/test_ptree/regular.zip',                        '',                                                                   '215d10a57cfd97756599b4bd93a06655', None, None, None, None],
        [21, '{cwd}/test_ptree/regular.zip',                        'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',                           '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500, 375],
        [22, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-cat-looks-like-an-owl.jpg',                           'bd914f72d824d2a18d076f7643017505', -93277392328150, None, 492, 442],
        [23, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-cat-will-do-science.jpg',                             '5b5620b0cfcb469aef632864707a0445', -5208810276318177639, None, 500, 674],
        [24, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-kitten-rules-a-tower.jpg',                            'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500, 375],
        [25, '{cwd}/test_ptree/small.zip',                          '',                                                                   'a7ff921ad3fe255dd459613ae096bb5a', None, None, None, None],
        [26, '{cwd}/test_ptree/small.zip',                          'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png',                        'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375, 281],
        [27, '{cwd}/test_ptree/small.zip',                          'funny-pictures-cat-looks-like-an-owl-ps.png',                        '740555f4e730ab2c6c261be7d53a3156', -93277392328150, None, 369, 332],
        [28, '{cwd}/test_ptree/small.zip',                          'funny-pictures-cat-will-do-science-ps.png',                          'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780925024615, None, 375, 506],
        [29, '{cwd}/test_ptree/small.zip',                          'funny-pictures-kitten-rules-a-tower-ps.png',                         'fb64248009dde8605a95b041b772544a', -5860684349360469885, None, 375, 281],
        [30, '{cwd}/test_ptree/small.zip',                          'superheroes-batman-superman-i-would-watch-the-hell-out-of-this.jpg', '083e179ff11ccf90a0d514651c69c2ca', -8034280126218048380, None, 200, 297],
        [31, '{cwd}/test_ptree/small_and_regular.zip',              '',                                                                   'd2ff4ff1f8345abf26a98abcc5710583', None, None, None, None],
        [32, '{cwd}/test_ptree/small_and_regular.zip',              'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png',                        'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375, 281],
        [33, '{cwd}/test_ptree/small_and_regular.zip',              'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',                           '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500,375],
        [34, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-looks-like-an-owl-ps.png',                        '740555f4e730ab2c6c261be7d53a3156', -93277392328150, None, 369, 332],
        [35, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-looks-like-an-owl.jpg',                           'bd914f72d824d2a18d076f7643017505', -93277392328150, None, 492, 442],
        [36, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-will-do-science-ps.png',                          'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780925024615, None, 375, 506],
        [37, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-will-do-science.jpg',                             '5b5620b0cfcb469aef632864707a0445', -5208810276318177639, None, 500, 674],
        [38, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-kitten-rules-a-tower-ps.png',                         'fb64248009dde8605a95b041b772544a', -5860684349360469885, None, 375, 281],
        [39, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-kitten-rules-a-tower.jpg',                            'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500, 375],
        [40, '{cwd}/test_ptree/small_and_regular_half_common.zip',  '',                                                                   '1d7162894bfe2fb724fa489e742d650e', None, None, None, None],
        [41, '{cwd}/test_ptree/small_and_regular_half_common.zip',  '718933691_2b0100d6d4_o.png',                                         '8952f5ece2f5867c3ff2b6e8a55db21f', 6151740457728939285, None, 507, 679],
        [42, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'CatT.png',                                                           '5f0aba1e6d1a7cf66c722f0fddb7ed18', 6944046409214920013, None, 125, 201],
        [43, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'circuit_diagram.png',                                                '494b166f7729f18906fae08d6bb93022', 7183957061339002, None, 740, 952],
        [44, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png',                        'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375, 281],
        [45, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',                           '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500, 375],
        [46, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'funny-pictures-cat-looks-like-an-owl-ps.png',                        '740555f4e730ab2c6c261be7d53a3156', -93277392328150, None, 369, 332],
        [47, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'funny-pictures-cat-looks-like-an-owl.jpg',                           'bd914f72d824d2a18d076f7643017505', -93277392328150, None, 492, 442],
        [48, '{cwd}/test_ptree/testArch.zip',                       '',                                                                   '86975a1f7fca8d520fb0bd4a29b1e953', None, None, None, None],
        [49, '{cwd}/test_ptree/testArch.zip',                       'Lolcat_this_is_mah_job.png',                                         '1268e704908cc39299d73d6caafc23a0', 27427800275512429, None, 493, 389],
        [50, '{cwd}/test_ptree/testArch.zip',                       'Lolcat_this_is_mah_job_small.jpg',                                   '40d39c436e14282dcda06e8aff367307', 27427800275512429, None, 300, 237],
        [51, '{cwd}/test_ptree/testArch.zip',                       'dangerous-to-go-alone.jpg',                                          'dcd6097eeac911efed3124374f44085b', -149413575039568585, None, 325, 307],
        [52, '{cwd}/test_ptree/z_reg.zip',                          '',                                                                   'faf60ecccdd0a854192b05d05aaa6a94', None, None, None, None],
        [53, '{cwd}/test_ptree/z_reg.zip',                          '129165237051396578.jpg',                                             'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332, 497],
        [54, '{cwd}/test_ptree/z_reg.zip',                          'test.txt',                                                           'b3a79c95a10b4cc0a838b35782b4dc0a', None, None, None, None],
        [55, '{cwd}/test_ptree/z_reg_junk.zip',                     '',                                                                   '1db2ae8cc01fa4d4f44b27e36ac14ad5', None, None, None, None],
        [56, '{cwd}/test_ptree/z_reg_junk.zip',                     '129165237051396578.jpg',                                             'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332, 497],
        [57, '{cwd}/test_ptree/z_reg_junk.zip',                     'Thumbs.db',                                                          '2ea0b76437adb1dfb8889beab9d7ef3b', None, None, None, None],
        [58, '{cwd}/test_ptree/z_reg_junk.zip',                     '__MACOSX/test.txt',                                                  '1ad84adee17e7d3525528ff7e381a900', None, None, None, None],
        [59, '{cwd}/test_ptree/z_reg_junk.zip',                     'deleted.txt',                                                        '2fe06876bc7694a6357e5d9c5f05e0ab', None, None, None, None],
        [60, '{cwd}/test_ptree/z_reg_junk.zip',                     'test.txt',                                                           'b3a79c95a10b4cc0a838b35782b4dc0a', None, None, None, None],
        [61, '{cwd}/test_ptree/z_sml.zip',                          '',                                                                   'c933bdb08eea6809a5cd06915edc1822', None, None, None, None],
        [62, '{cwd}/test_ptree/z_sml.zip',                          '129165237051396578(s).jpg',                                          '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249, 373],
        [63, '{cwd}/test_ptree/z_sml.zip',                          'test.txt',                                                           'b3a79c95a10b4cc0a838b35782b4dc0a', None, None, None, None],
        [64, '{cwd}/test_ptree/z_sml_u.zip',                        '',                                                                   '352e67b2b64a139a6bd413b8ea4235ca', None, None, None, None],
        [65, '{cwd}/test_ptree/z_sml_u.zip',                        '129165237051396578(s).jpg',                                          '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249, 373],
        [66, '{cwd}/test_ptree/z_sml_u.zip',                        'test.txt',                                                           '1234ae2e7a21c94100cb60773efe482b', None, None, None, None],
        [67, '{cwd}/test_ptree/z_sml_w.zip',                        '',                                                                   'd51ce2bb73dafd7bb769e2fee7d195c5', None, None, None, None],
        [68, '{cwd}/test_ptree/z_sml_w.zip',                        '129165237051396578(s).jpg',                                          'e8566233d43b2e964b77471a99c5fa36', 0, None, 100, 100],
        [69, '{cwd}/test_ptree/z_sml_w.zip',                        'test.txt',                                                           'b3a79c95a10b4cc0a838b35782b4dc0a', None, None, None, None],


	# [1,  '{cwd}/test_ptree/allArch.zip',                        '',                                            '9d7d02a6bff693737904c5d1a35c89cc', None,                 None, None, None],
	# [2,  '{cwd}/test_ptree/allArch.zip',                        'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    None, 493,  389],
	# [3,  '{cwd}/test_ptree/allArch.zip',                        'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	# [4,  '{cwd}/test_ptree/allArch.zip',                        'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	# [5,  '{cwd}/test_ptree/allArch.zip',                        'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  None, 325,  307],
	# [6,  '{cwd}/test_ptree/allArch.zip',                        'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
	# [7,  '{cwd}/test_ptree/allArch.zip',                        'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501,  356],
	# [8,  '{cwd}/test_ptree/notQuiteAllArch.zip',                '',                                            'd3c2108bfc69602cfbf2f821eb874ccd', None,                 None, None, None],
	# [9,  '{cwd}/test_ptree/notQuiteAllArch.zip',                'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    None, 493,  389],
	# [10, '{cwd}/test_ptree/notQuiteAllArch.zip',                'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	# [11, '{cwd}/test_ptree/notQuiteAllArch.zip',                'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	# [12, '{cwd}/test_ptree/notQuiteAllArch.zip',                'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
	# [13, '{cwd}/test_ptree/notQuiteAllArch.zip',                'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501,  356],
	# [14, '{cwd}/test_ptree/regular.zip',                        '',                                            '215d10a57cfd97756599b4bd93a06655', None,                 None, None, None],
	# [15, '{cwd}/test_ptree/regular.zip',                        'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500,  375],
	# [16, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      None, 492,  442],
	# [17, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-cat-will-do-science.jpg',      '5b5620b0cfcb469aef632864707a0445', -5208810276318177639, None, 500,  674],
	# [18, '{cwd}/test_ptree/regular.zip',                        'funny-pictures-kitten-rules-a-tower.jpg',     'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500,  375],
	# [19, '{cwd}/test_ptree/small.zip',                          '',                                            'e03de591503f67302f77dad9e0a80669', None,                 None, None, None],
	# [20, '{cwd}/test_ptree/small.zip',                          'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375,  281],
	# [21, '{cwd}/test_ptree/small.zip',                          'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      None, 369,  332],
	# [22, '{cwd}/test_ptree/small.zip',                          'funny-pictures-cat-will-do-science-ps.png',   'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780925024615, None, 375,  506],
	# [23, '{cwd}/test_ptree/small.zip',                          'funny-pictures-kitten-rules-a-tower-ps.png',  'fb64248009dde8605a95b041b772544a', -5860684349360469885, None, 375,  281],
	# [24, '{cwd}/test_ptree/small_and_regular.zip',              '',                                            'd2ff4ff1f8345abf26a98abcc5710583', None,                 None, None, None],
	# [25, '{cwd}/test_ptree/small_and_regular.zip',              'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375,  281],
	# [26, '{cwd}/test_ptree/small_and_regular.zip',              'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500,  375],
	# [27, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      None, 369,  332],
	# [28, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      None, 492,  442],
	# [29, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-will-do-science-ps.png',   'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780925024615, None, 375,  506],
	# [30, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-cat-will-do-science.jpg',      '5b5620b0cfcb469aef632864707a0445', -5208810276318177639, None, 500,  674],
	# [31, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-kitten-rules-a-tower-ps.png',  'fb64248009dde8605a95b041b772544a', -5860684349360469885, None, 375,  281],
	# [32, '{cwd}/test_ptree/small_and_regular.zip',              'funny-pictures-kitten-rules-a-tower.jpg',     'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500,  375],
	# [33, '{cwd}/test_ptree/small_and_regular_half_common.zip',  '',                                            '1d7162894bfe2fb724fa489e742d650e', None,                 None, None, None],
	# [34, '{cwd}/test_ptree/small_and_regular_half_common.zip',  '718933691_2b0100d6d4_o.png',                  '8952f5ece2f5867c3ff2b6e8a55db21f', 6151740457728939285,  None, 507,  679],
	# [35, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'CatT.png',                                    '5f0aba1e6d1a7cf66c722f0fddb7ed18', 6944046409214920013,  None, 125,  201],
	# [36, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'circuit_diagram.png',                         '494b166f7729f18906fae08d6bb93022', 7183957061339002,     None, 740,  952],
	# [37, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375,  281],
	# [38, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500,  375],
	# [39, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      None, 369,  332],
	# [40, '{cwd}/test_ptree/small_and_regular_half_common.zip',  'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      None, 492,  442],
	# [41, '{cwd}/test_ptree/testArch.zip',                       '',                                            '86975a1f7fca8d520fb0bd4a29b1e953', None,                 None, None, None],
	# [42, '{cwd}/test_ptree/testArch.zip',                       'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	# [43, '{cwd}/test_ptree/testArch.zip',                       'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	# [44, '{cwd}/test_ptree/testArch.zip',                       'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  None, 325,  307],
	# [45, '{cwd}/test_ptree/z_reg.zip',                          '',                                            'faf60ecccdd0a854192b05d05aaa6a94', None,                 None, None, None],
	# [46, '{cwd}/test_ptree/z_reg.zip',                          '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332,  497],
	# [47, '{cwd}/test_ptree/z_reg.zip',                          'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	# [48, '{cwd}/test_ptree/z_reg_junk.zip',                     '',                                            '1db2ae8cc01fa4d4f44b27e36ac14ad5', None,                 None, None, None],
	# [49, '{cwd}/test_ptree/z_reg_junk.zip',                     '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332,  497],
	# [50, '{cwd}/test_ptree/z_reg_junk.zip',                     'Thumbs.db',                                   '2ea0b76437adb1dfb8889beab9d7ef3b', None,                 None, None, None],
	# [51, '{cwd}/test_ptree/z_reg_junk.zip',                     '__MACOSX/test.txt',                           '1ad84adee17e7d3525528ff7e381a900', None,                 None, None, None],
	# [52, '{cwd}/test_ptree/z_reg_junk.zip',                     'deleted.txt',                                 '2fe06876bc7694a6357e5d9c5f05e0ab', None,                 None, None, None],
	# [53, '{cwd}/test_ptree/z_reg_junk.zip',                     'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	# [54, '{cwd}/test_ptree/z_sml.zip',                          '',                                            'c933bdb08eea6809a5cd06915edc1822', None,                 None, None, None],
	# [55, '{cwd}/test_ptree/z_sml.zip',                          '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249,  373],
	# [56, '{cwd}/test_ptree/z_sml.zip',                          'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	# [57, '{cwd}/test_ptree/z_sml_u.zip',                        '',                                            '352e67b2b64a139a6bd413b8ea4235ca', None,                 None, None, None],
	# [58, '{cwd}/test_ptree/z_sml_u.zip',                        '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249,  373],
	# [59, '{cwd}/test_ptree/z_sml_u.zip',                        'test.txt',                                    '1234ae2e7a21c94100cb60773efe482b', None,                 None, None, None],
	# [60, '{cwd}/test_ptree/z_sml_w.zip',                        '',                                            'd51ce2bb73dafd7bb769e2fee7d195c5', None,                 None, None, None],
	# [61, '{cwd}/test_ptree/z_sml_w.zip',                        '129165237051396578(s).jpg',                   'e8566233d43b2e964b77471a99c5fa36', 0,                    None, 100,  100],
	# [62, '{cwd}/test_ptree/z_sml_w.zip',                        'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],




]

# Patch in current script directory so the CONTENTS paths work.
curdir = os.path.dirname(os.path.realpath(__file__))
for x in range(len(CONTENTS)):
	CONTENTS[x][1] = CONTENTS[x][1].format(cwd=curdir)
	CONTENTS[x] = tuple(CONTENTS[x])



