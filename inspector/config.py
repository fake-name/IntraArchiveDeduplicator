


import os
import sys
import datetime

import string
import random

random.seed()

if len(sys.argv) > 1 and "debug" in sys.argv:
	SQLALCHEMY_ECHO = True


REFETCH_INTERVAL = datetime.timedelta(days=7*3)

basedir = os.path.abspath(os.path.dirname(__file__))

def get_random(chars):
	rand = [random.choice(string.ascii_letters) for x in range(chars)]
	rand = "".join(rand)
	return rand


class BaseConfig(object):

	ADMINS = ['you@example.com']

	SEND_FILE_MAX_AGE_DEFAULT = 60*60*12

	# The WTF protection doesn't have to persist across
	# execution sessions, since that'll break any
	# active sessions anyways. Therefore, just generate
	# them randomly at each start.
	SECRET_KEY             = get_random(20)

