
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
import time
import datetime
from calendar import timegm

from . import reader_session_manager
from inspector import app
from inspector import db_pool

def guessItemMimeType(itemName):
	mime_type = mimetypes.guess_type(itemName)
	print("Inferred MIME type %s for file %s" % (mime_type,  itemName))
	if mime_type:
		return mime_type[0]
	return "application/unknown"

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
					200;""", (phash, dist))

			matches[dist] = cur.fetchall()
			print("Returned %s items" % (len(matches[dist]), ))

	return matches

def get_deduper_resource(rowid):
	matches = {}
	with db_pool.db_cursor() as cur:
		cur.execute("""
			SELECT
				fspath,
				internalpath
			FROM
				dedupitems
			WHERE
				dbid = %s
			;""", (rowid, ))

		row = cur.fetchone()

	print("Row: ", row)

	if not row:
		flash('Series id %s not found!' % rowid)
		return redirect(url_for('high_incidence_items'))

	fspath, intpath = row
	if fspath and not intpath:
		with open(fspath, "rb") as itemFileHandle:
			response = make_response(itemFileHandle.read())
			response.headers['Content-Type']        = guessItemMimeType(fspath)
			response.headers['Content-Disposition'] = "inline; filename=" + fspath.split("/")[-1]
			return response

	elif fspath and intpath:
		session_manager = reader_session_manager.SessionPoolManager()
		session_manager[("dd", rowid)].checkOpenArchive(fspath)
		itemFileHandle, _ = session_manager[("dd", rowid)].getItemByInternalPath(intpath)

		response = make_response(itemFileHandle.read())
		response.headers['Content-Type']        = guessItemMimeType(intpath)
		response.headers['Content-Disposition'] = "inline; filename=" + intpath.split("/")[-1]
		return response


	else:
		flash('Series id %s not found!' % rowid)
		return redirect(url_for('high_incidence_items'))


@app.route('/debug/high_incidence_items', methods=['GET'])
def high_incidence_items():
	common = get_high_incidence_issues()

	return render_template('overcommon_files.html',
						   common          = common,
						   )

@app.route('/debug/high_incidence_item/<int:phash>', methods=['GET'])
def high_incidence_item(phash):
	matches = get_high_incidence_item(phash)

	return render_template('overcommon_file.html',
						   matches          = matches,
						   )

@app.route('/debug/scraper_resource/<int:rowid>', methods=['GET'])
def high_incidence_resource(rowid):
	return get_deduper_resource(rowid)



