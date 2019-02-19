#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging
import multiprocessing
import settings
import tqdm


from neo4j import GraphDatabase



def add_phash4_link(tx, from_rid, from_fspath, from_intpath, to_rid, to_fspath, to_intpath):
	if from_rid != to_rid:
		tx.run("MERGE (from_node:FileNode {rid: $from_rid, fspath: $from_fspath, intpath: $from_intpath}) "
			   "MERGE (  to_node:FileNode {rid: $to_rid,   fspath: $to_fspath,   intpath: $to_intpath})"
			   "MERGE (from_node)-[:Phash4]-(to_node)"
			   ,
					from_rid     = from_rid,
					from_fspath  = from_fspath,
					from_intpath = from_intpath,
					to_rid       = to_rid,
					to_fspath    = to_fspath,
					to_intpath   = to_intpath,
			   )

	# if from_fspath != to_fspath:
	# 	tx.run("MERGE (from_fnode:FileNode {fspath: $from_fspath}) "
	# 		   "MERGE (  to_fnode:FileNode {fspath: $to_fspath})"
	# 		   "MERGE (from_fnode)-[:archive]-(to_fnode)"
	# 		   ,
	# 				from_fspath  = from_fspath,
	# 				to_fspath    = to_fspath,
	# 		   )

def insert_entries(tx, item_tups):

	for row_id, row_fspath, row_intpath in item_tups:
		tx.run("MERGE (from_node:FileNode {rid: $rid, fspath: $fspath, intpath: $intpath}) "
			   ,
					rid     = row_id,
					fspath  = row_fspath,
					intpath = row_intpath,
			   )


def add_link_sets(tx, link_sets):

	for item1_tup, item2_tup in link_sets:
		if item2_tup:
			rid_1, fspath_1, intpath_1 = item1_tup
			rid_2, fspath_2, intpath_2 = item2_tup
			add_phash4_link(tx, rid_1, fspath_1, intpath_1, rid_2, fspath_2, intpath_2)
		else:
			insert_entries(tx, (item1_tup, ))


class GraphApi():
	loggerPath = "Main.GraphApi"

	def __init__(self):

		# If we're running as a multiprocessing thread, inject that into
		# the logger path
		threadName = multiprocessing.current_process().name
		if threadName:
			self.log = logging.getLogger("%s.%s" % (self.loggerPath, threadName))
		else:
			self.log = logging.getLogger(self.loggerPath)

		self._driver = GraphDatabase.driver(settings.GRAPH_DATABASE_URI, auth=(settings.GRAPH_DATABASE_USER, settings.GRAPH_DATABASE_PASS))

	def close(self):
		self._driver.close()

	def insert_entry_bulk(self, item_tups):

		with self._driver.session() as sess:
			sess.write_transaction(insert_entries,
					item_tups    = item_tups,
				)

	def insert_link(self, item1_tup, item2_tup):
		rid_1, fspath_1 = item1_tup
		rid_2, fspath_2 = item2_tup

		with self._driver.session() as sess:
			sess.write_transaction(add_phash4_link,
					from_rid     = rid_1,
					from_fspath  = fspath_1,
					to_rid       = rid_2,
					to_fspath    = fspath_2,
				)


	def insert_link_batch(self, link_sets):
		with self._driver.session() as sess:
			sess.write_transaction(add_link_sets,
					link_sets     = link_sets,
				)

def test():
	ind = GraphApi()

	item1 = (1, "aaaa1")
	item2 = (2, "aaaa2")
	item3 = (3, "aaaa1")
	item4 = (4, "aaaa2")
	item5 = (5, "aaaa1")
	item6 = (6, "aaaa2")
	item7 = (7, "aaaa1")
	item8 = (8, "aaaa2")

	ind.insert_link(item1, item2)
	ind.insert_link(item2, item3)
	ind.insert_link(item3, item4)
	ind.insert_link(item4, item5)
	ind.insert_link(item5, item6)
	ind.insert_link(item6, item7)
	ind.insert_link(item7, item8)
	ind.insert_link(item8, item1)


if __name__ == "__main__":

	import scanner.logSetup
	scanner.logSetup.initLogging()
	test()

