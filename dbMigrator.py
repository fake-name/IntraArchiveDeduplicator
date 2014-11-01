
import dbApi
import logging
import logSetup

import sql.operators as sqlo
import unitConverters


def migrate():
	api = dbApi.DbApi()
	print("Api = ", api)

	where = (api.table.phash_text != None)
	print("Fetching rows to convert")
	items = api.getItems(wantCols=['dbId', 'phash_text', 'dhash_text', 'phash', 'dhash'], where=where)
	print("items", len(items))

	rowCount = 0

	cur = api.conn.cursor()
	cur.execute("BEGIN;")
	for dbId, pHash_text, dHash_text, pHash_orig, dHash_orig in items:
		pHash = unitConverters.binStrToInt(pHash_text)
		dHash = unitConverters.binStrToInt(dHash_text)
		rowCount += 1


		if pHash != pHash_orig or dHash != dHash_orig:
			try:
				# Doing manual SQL queries because the overhead of the dynamic queries is just too much.
				cur.execute("UPDATE dedupitems SET phash=%s, dhash=%s WHERE dbid=%s;", (pHash, dHash, dbId))
			except:
				print("Wat?")
				print(pHash)
				print(pHash_text)
				print(dHash)
				print(dHash_text)
				raise


		if rowCount % 5000 == 0:
			print("loop", rowCount)
			cur.execute("COMMIT;")
			cur.execute("BEGIN;")
			print("Committed")

	cur.execute("COMMIT;")
	# api.updateDbEntry(dbId=dbId, pHash=pHash, dHash=dHash, commit=False)

if __name__ == "__main__":
	logSetup.initLogging()
	migrate()



