
import dbApi
import logging
import logSetup

import sql.operators as sqlo

def binStrToInt(inStr):
	ret = 0
	mask = 1 << len(inStr) - 1
	for char in inStr:  # Specify memory order, so we're (theoretically) platform agnostic
		if char == '1':
			ret |= mask
		mask >>= 1

	# Convert to signed representation
	VALSIZE = 64
	if ret >= 2**(VALSIZE-1):
		ret = ret - 2**VALSIZE
	return ret



def migrate():
	api = dbApi.DbApi()
	print("Api = ", api)

	where = (api.table.phash_text != None)
	print("Fetching rows to convert")
	items = api.getItems(wantCols=['dbId', 'phash_text', 'dhash_text'], where=where)
	print("items", len(items))

	rowCount = 0

	cur = api.conn.cursor()
	cur.execute("BEGIN;")
	for dbId, pHash_text, dHash_text in items:
		pHash = binStrToInt(pHash_text)
		dHash = binStrToInt(dHash_text)
		rowCount += 1

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



