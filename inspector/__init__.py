
import os
import uuid
import time
import string
import random
import datetime
import urllib.parse
import sys
from ipaddress import IPv4Address, IPv4Network
import settings

from flask import Flask
from flask import g
from flask import request
from babel.dates import format_datetime


print("App import!")

app = Flask(__name__)

if "debug" in sys.argv:
	print("Flask running in debug mode!")
	app.debug = True
	app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))


app.config.from_object('inspector.config.BaseConfig')


from . import views


app.jinja_env.globals.update(
		# plugin_key_for_name   = plugin_key_for_name,
	)

