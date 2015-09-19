
'''
This file contains what the DB should contain after all the files in the test_ptree directory are hashed.

All test images are lolcats. AS GOD INTENDED.

'''

import os
import os.path

def insertCwd(inStr):
	cwd = os.path.dirname(os.path.realpath(__file__))
	inStr = inStr.format(cwd=cwd)
	return inStr


# [1,  '{cwd}/test_ptree/allArch.zip',         '',                                            '9d7d02a6bff693737904c5d1a35c89cc', None,                  None,                None, None, None],
# [2,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    -4504585791368671746, None, 493,  389],
# [3,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
# [4,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
# [5,  '{cwd}/test_ptree/allArch.zip',         'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,   4576150637722077151, None, 325,  307],
# [6,  '{cwd}/test_ptree/allArch.zip',         'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279,  167400391896309758,  None, 500,  363],
# [7,  '{cwd}/test_ptree/allArch.zip',         'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, -8660145558008088574, None, 501,  356],
# [8,  '{cwd}/test_ptree/notQuiteAllArch.zip', '',                                            'd3c2108bfc69602cfbf2f821eb874ccd', None,                  None,                None, None, None],
# [9,  '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    -4504585791368671746, None, 493,  389],
# [10, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
# [11, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
# [12, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279,  167400391896309758,  None, 500,  363],
# [13, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, -8660145558008088574, None, 501,  356],
# [14, '{cwd}/test_ptree/regular.zip',         '',                                            '215d10a57cfd97756599b4bd93a06655', None,                  None,                None, None, None],
# [15, '{cwd}/test_ptree/regular.zip',         'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758,  5546533486212567551, None, 500,  375],
# [16, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      -4629305759067799552, None, 492,  442],
# [17, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-will-do-science.jpg',      '5b5620b0cfcb469aef632864707a0445', -6361731780925024615,  1119025673978783491, None, 500,  674],
# [18, '{cwd}/test_ptree/regular.zip',         'funny-pictures-kitten-rules-a-tower.jpg',     'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885,  9187567978625498130, None, 500,  375],
# [19, '{cwd}/test_ptree/small.zip',           '',                                            'e03de591503f67302f77dad9e0a80669',        None,           None,                None, None, None],
# [20, '{cwd}/test_ptree/small.zip',           'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758,  5546533486212567551, None, 375,  281],
# [21, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      -4629305759067799552, None, 369,  332],
# [22, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-will-do-science-ps.png',   'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780920830311,  1119025673978783491, None, 375,  506],
# [23, '{cwd}/test_ptree/small.zip',           'funny-pictures-kitten-rules-a-tower-ps.png',  'fb64248009dde8605a95b041b772544a', -5860684349360469885,  9187567978625498130, None, 375,  281],
# [24, '{cwd}/test_ptree/testArch.zip',        '',                                            '86975a1f7fca8d520fb0bd4a29b1e953', None,                  None,                None, None, None],
# [25, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    -4504585791368671746, None, 493,  389],
# [26, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    -4504585791368671746, None, 300,  237],
# [27, '{cwd}/test_ptree/testArch.zip',        'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,   4576150637722077151, None, 325,  307],
# [28, '{cwd}/test_ptree/z_reg.zip',           '',                                            'faf60ecccdd0a854192b05d05aaa6a94', None,                  None,                None, None, None],
# [29, '{cwd}/test_ptree/z_reg.zip',           '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257,  4593710720968564225, None, 332,  497],
# [30, '{cwd}/test_ptree/z_reg.zip',           'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                  None,                None, None, None],
# [31, '{cwd}/test_ptree/z_reg_junk.zip',      '',                                            '1db2ae8cc01fa4d4f44b27e36ac14ad5', None,                  None,                None, None, None],
# [32, '{cwd}/test_ptree/z_reg_junk.zip',      '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257,  4593710720968564225, None, 332,  497],
# [33, '{cwd}/test_ptree/z_reg_junk.zip',      'Thumbs.db',                                   '2ea0b76437adb1dfb8889beab9d7ef3b', None,                  None,                None, None, None],
# [34, '{cwd}/test_ptree/z_reg_junk.zip',      '__MACOSX/test.txt',                           '1ad84adee17e7d3525528ff7e381a900', None,                  None,                None, None, None],
# [35, '{cwd}/test_ptree/z_reg_junk.zip',      'deleted.txt',                                 '2fe06876bc7694a6357e5d9c5f05e0ab', None,                  None,                None, None, None],
# [36, '{cwd}/test_ptree/z_reg_junk.zip',      'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                  None,                None, None, None],
# [37, '{cwd}/test_ptree/z_sml.zip',           '',                                            'c933bdb08eea6809a5cd06915edc1822', None,                  None,                None, None, None],
# [38, '{cwd}/test_ptree/z_sml.zip',           '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257,  4593710720834346496, None, 249,  373],
# [39, '{cwd}/test_ptree/z_sml.zip',           'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                  None,                None, None, None],
# [40, '{cwd}/test_ptree/z_sml_u.zip',         '',                                            '352e67b2b64a139a6bd413b8ea4235ca', None,                  None,                None, None, None],
# [41, '{cwd}/test_ptree/z_sml_u.zip',         '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257,  4593710720834346496, None, 249,  373],
# [42, '{cwd}/test_ptree/z_sml_u.zip',         'test.txt',                                    '1234ae2e7a21c94100cb60773efe482b', None,                  None,                None, None, None],
# [43, '{cwd}/test_ptree/z_sml_w.zip',         '',                                            'd51ce2bb73dafd7bb769e2fee7d195c5', None,                  None,                None, None, None],
# [44, '{cwd}/test_ptree/z_sml_w.zip',         '129165237051396578(s).jpg',                   'e8566233d43b2e964b77471a99c5fa36', 0,                     0,                   None, 100,  100],
# [45, '{cwd}/test_ptree/z_sml_w.zip',         'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                  None,                None, None, None],

CONTENTS = [
	[1,  '{cwd}/test_ptree/allArch.zip',         '',                                            '9d7d02a6bff693737904c5d1a35c89cc', None,                 None, None, None],
	[2,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    None, 493,  389],
	[3,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	[4,  '{cwd}/test_ptree/allArch.zip',         'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	[5,  '{cwd}/test_ptree/allArch.zip',         'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  None, 325,  307],
	[6,  '{cwd}/test_ptree/allArch.zip',         'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
	[7,  '{cwd}/test_ptree/allArch.zip',         'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501,  356],
	[8,  '{cwd}/test_ptree/notQuiteAllArch.zip', '',                                            'd3c2108bfc69602cfbf2f821eb874ccd', None,                 None, None, None],
	[9,  '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.jpg',                  'd9ceeb6b43c2d7d096532eabfa6cf482', 27427800275512429,    None, 493,  389],
	[10, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	[11, '{cwd}/test_ptree/notQuiteAllArch.zip', 'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	[12, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-crocs.jpg',                            '6d0a977694630ac9d1d33a7f068e10f8', -5569898607211671279, None, 500,  363],
	[13, '{cwd}/test_ptree/notQuiteAllArch.zip', 'lolcat-oregon-trail.jpg',                     '7227289a017988b6bdcf61fd4761f6b9', -4955310669995365332, None, 501,  356],
	[14, '{cwd}/test_ptree/regular.zip',         '',                                            '215d10a57cfd97756599b4bd93a06655', None,                 None, None, None],
	[15, '{cwd}/test_ptree/regular.zip',         'e61ec521-155d-4a3a-956d-2544d4367e02.jpg',    '35484890b48148d260b52ebbb7493ffc', -4230769653536099758, None, 500,  375],
	[16, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-looks-like-an-owl.jpg',    'bd914f72d824d2a18d076f7643017505', -93277392328150,      None, 492,  442],
	[17, '{cwd}/test_ptree/regular.zip',         'funny-pictures-cat-will-do-science.jpg',      '5b5620b0cfcb469aef632864707a0445', -6361731780925024615, None, 500,  674],
	[18, '{cwd}/test_ptree/regular.zip',         'funny-pictures-kitten-rules-a-tower.jpg',     'a26d63bdbb38621b8f44c563ff496987', -5860684349360469885, None, 500,  375],
	[19, '{cwd}/test_ptree/small.zip',           '',                                            'e03de591503f67302f77dad9e0a80669',        None,          None, None, None],
	[20, '{cwd}/test_ptree/small.zip',           'e61ec521-155d-4a3a-956d-2544d4367e02-ps.png', 'b4c3d02411a34e1222972cc262a40b89', -4230769653536099758, None, 375,  281],
	[21, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-looks-like-an-owl-ps.png', '740555f4e730ab2c6c261be7d53a3156', -93277392328150,      None, 369,  332],
	[22, '{cwd}/test_ptree/small.zip',           'funny-pictures-cat-will-do-science-ps.png',   'c47ed1cd79c4e7925b8015cb51bbab10', -6361731780920830311, None, 375,  506],
	[23, '{cwd}/test_ptree/small.zip',           'funny-pictures-kitten-rules-a-tower-ps.png',  'fb64248009dde8605a95b041b772544a', -5860684349360469885, None, 375,  281],
	[24, '{cwd}/test_ptree/testArch.zip',        '',                                            '86975a1f7fca8d520fb0bd4a29b1e953', None,                 None, None, None],
	[25, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job.png',                  '1268e704908cc39299d73d6caafc23a0', 27427800275512429,    None, 493,  389],
	[26, '{cwd}/test_ptree/testArch.zip',        'Lolcat_this_is_mah_job_small.jpg',            '40d39c436e14282dcda06e8aff367307', 27427800275512429,    None, 300,  237],
	[27, '{cwd}/test_ptree/testArch.zip',        'dangerous-to-go-alone.jpg',                   'dcd6097eeac911efed3124374f44085b', -149413575039568585,  None, 325,  307],
	[28, '{cwd}/test_ptree/z_reg.zip',           '',                                            'faf60ecccdd0a854192b05d05aaa6a94', None,                 None, None, None],
	[29, '{cwd}/test_ptree/z_reg.zip',           '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332,  497],
	[30, '{cwd}/test_ptree/z_reg.zip',           'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	[31, '{cwd}/test_ptree/z_reg_junk.zip',      '',                                            '1db2ae8cc01fa4d4f44b27e36ac14ad5', None,                 None, None, None],
	[32, '{cwd}/test_ptree/z_reg_junk.zip',      '129165237051396578.jpg',                      'b688e3ead00ca1453f860b408c446ec2', -5788352938335285257, None, 332,  497],
	[33, '{cwd}/test_ptree/z_reg_junk.zip',      'Thumbs.db',                                   '2ea0b76437adb1dfb8889beab9d7ef3b', None,                 None, None, None],
	[34, '{cwd}/test_ptree/z_reg_junk.zip',      '__MACOSX/test.txt',                           '1ad84adee17e7d3525528ff7e381a900', None,                 None, None, None],
	[35, '{cwd}/test_ptree/z_reg_junk.zip',      'deleted.txt',                                 '2fe06876bc7694a6357e5d9c5f05e0ab', None,                 None, None, None],
	[36, '{cwd}/test_ptree/z_reg_junk.zip',      'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	[37, '{cwd}/test_ptree/z_sml.zip',           '',                                            'c933bdb08eea6809a5cd06915edc1822', None,                 None, None, None],
	[38, '{cwd}/test_ptree/z_sml.zip',           '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249,  373],
	[39, '{cwd}/test_ptree/z_sml.zip',           'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],
	[40, '{cwd}/test_ptree/z_sml_u.zip',         '',                                            '352e67b2b64a139a6bd413b8ea4235ca', None,                 None, None, None],
	[41, '{cwd}/test_ptree/z_sml_u.zip',         '129165237051396578(s).jpg',                   '7c257ec7fdfd24f249d290dc47dcc71c', -5788352938335285257, None, 249,  373],
	[42, '{cwd}/test_ptree/z_sml_u.zip',         'test.txt',                                    '1234ae2e7a21c94100cb60773efe482b', None,                 None, None, None],
	[43, '{cwd}/test_ptree/z_sml_w.zip',         '',                                            'd51ce2bb73dafd7bb769e2fee7d195c5', None,                 None, None, None],
	[44, '{cwd}/test_ptree/z_sml_w.zip',         '129165237051396578(s).jpg',                   'e8566233d43b2e964b77471a99c5fa36', 0,                    None, 100,  100],
	[45, '{cwd}/test_ptree/z_sml_w.zip',         'test.txt',                                    'b3a79c95a10b4cc0a838b35782b4dc0a', None,                 None, None, None],



]

# Patch in current script directory so the CONTENTS paths work.
curdir = os.path.dirname(os.path.realpath(__file__))
for x in range(len(CONTENTS)):
	CONTENTS[x][1] = CONTENTS[x][1].format(cwd=curdir)
	CONTENTS[x] = tuple(CONTENTS[x])



