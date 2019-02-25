#!/usr/bin/env python
# coding: utf-8

import logging
import tqdm
import dbPhashApi
import deduplicator.cyHamDb as cdb
import scanner.logSetup
import dbApi
import concurrent.futures

INSERT_CHUNK_SIZE_CONST = 250
SEARCH_SCOPE_CONST      = 4


def do_search(tree, search_dist, item_rid, item_phash):
	inserts = set()

	similar = tree.getWithinDistance(item_phash, search_dist)

	if similar:
		for other_rid in [tmp for tmp in similar if tmp != item_rid]:
			item_1, item_2 = min(item_rid, other_rid), max(item_rid, other_rid)
			inserts.add((item_1, item_2, search_dist))

	# else:
	# 	inserts.append(((item_rid, src_fspath, src_intpath), None))

	return inserts


class Importer():
	def __init__(self):
		self.log = logging.getLogger("Main.Importer")
		self.db = dbApi.DbApi()


	def get_entry_count(self):
		cur = self.db.conn.cursor()
		cur.execute("ROLLBACK")
		cur.execute("BEGIN")
		cur.execute("SELECT COUNT(*) FROM dedupitems")
		tot,  = cur.fetchone()

		self.log.info("Total entries in DB: %s", tot)

		return tot

	def load_db_entries(self):

		tot = self.get_entry_count()


		self.log.info("Streaming entries from database.")
		cur = self.db.conn.cursor()

		try:
			cur.execute("CLOSE streaming_item_fetch;")
		except Exception:
			cur.execute("ROLLBACK")

		cur.execute("COMMIT")
		cur.execute("BEGIN")

		ncur = self.db.conn.cursor("streaming_item_fetch")

		ncur.execute("select dbId, pHash FROM dedupitems")

		entries = {}

		for dbId, pHash in tqdm.tqdm(ncur, total=tot):
			if pHash:
				entries[dbId] = pHash

		cur.execute("CLOSE streaming_item_fetch;")
		cur.execute("COMMIT")

		return entries

	def build_tree(self, entries):
		self.log.info("Building tree with %s entries", len(entries))
		tree = cdb.CPPBkHammingTree()
		for key, phash in tqdm.tqdm(entries.items()):
			if phash:
				tree.unlocked_insert(phash, key)

		self.log.info("Tree built!")

		return tree

	def extract_edges(self, entries, tree, search_dist = SEARCH_SCOPE_CONST, chunk_size = INSERT_CHUNK_SIZE_CONST):
		seen       = set()
		insert_set = set()
		active     = {}
		links      = 0

		self.log.info("Doing search for edges on tree with %s entries.", len(entries))

		pbar = tqdm.tqdm(entries.items(), desc="Main Iteration")

		with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:

			for item_rid, value in pbar:
				res = executor.submit(do_search, tree, search_dist, item_rid, value)

				active[res] = None

				while len(active) > 50:
					for job in concurrent.futures.as_completed(active):
						tmp         = set(job.result())
						tmp         = tmp - seen
						insert_set |= tmp
						seen       |= tmp
						del active[job]


				while len(insert_set) > chunk_size:
					pbar.set_description("Links found: %s. Inserting %s" % (links, len(insert_set)))
					self.db.insert_phash_link_many(insert_set)
					links += len(insert_set)
					insert_set = set()


			self.db.insert_phash_link_many(insert_set)
			links += len(insert_set)
			insert_set = set()

			self.log.info("Inserted %s links", links)

def run_importer():

	importer = Importer()
	entries = importer.load_db_entries()
	tree = importer.build_tree(entries)
	importer.extract_edges(entries, tree)



if __name__ == "__main__":

	scanner.logSetup.initLogging(logLevel=logging.INFO)

	run_importer()


