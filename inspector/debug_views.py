
import mimetypes
from flask import g
from flask import render_template
from flask import make_response
from flask import request
from flask import flash
from flask import redirect
from flask import url_for

from tzlocal import get_localzone

import pickle
import bitstring
import time
import datetime
from calendar import timegm

from . import reader_session_manager
from inspector import app
from inspector import db_pool


def i2b(intval):

	bs = bitstring.BitArray(int=intval, length=64)
	return bs.bin



def get_high_incidence_issues():

	with db_pool.db_cursor() as cur:
		cur.execute('''
			SELECT
				dbid,
				phash,
				match_count,
				distance
			FROM
				high_incidence_hashes
			ORDER BY
				match_count DESC
			LIMIT
				5000
				;''')
		rets = cur.fetchall()
	rets = [
			( dbid, phash, i2b(phash), match_count, distance )
		for
			dbid, phash, match_count, distance
		in
			rets

	]
	return rets

def get_high_incidence_item(phash):
	matches = {}
	with db_pool.db_cursor() as cur:
		for dist in [0, 1, 2]:
			print("Doing search for %s with distance %s" % (phash, dist))
			cur.execute("""
				SELECT
					dbid,
					fspath,
					internalpath
				FROM
					dedupitems
				WHERE
					phash <@ (%s, %s)
				ORDER BY
					dbid ASC
				LIMIT
					100;""", (phash, dist))

			matches[dist] = cur.fetchall()
			print("Returned %s items" % (len(matches[dist]), ))

	return matches




@app.route('/debug/high_incidence_items', methods=['GET'])
def high_incidence_items():
	common = get_high_incidence_issues()

	return render_template('overcommon_files.html',
						   common          = common,
						   )

@app.route('/debug/high_incidence_item/<phash>', methods=['GET'])
def high_incidence_item(phash):

	try:
		phash = int(phash)
	except ValueError:
		flash('Phash %s not an integer!' % phash)
		return redirect(url_for('high_incidence_items'))

	matches = get_high_incidence_item(phash)

	return render_template('overcommon_file.html',
						   matches          = matches,
						   )

@app.route('/debug/single_item/<int:rowid>', methods=['GET'])
def single_image(rowid):
	return render_template('single_file.html',
						   rowid          = rowid,
						   )

