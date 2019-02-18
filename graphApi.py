#!/usr/bin/python
# -*- coding: utf-8 -*-


import logging
import multiprocessing
import settings


from neo4j import GraphDatabase



def add_phash4_link(tx, from_fqpath, from_rid, from_fspath, from_intpath, to_fqpath, to_rid, to_fspath, to_intpath):
	tx.run("MERGE (from_node:FileNode {fqpath: $from_fqpath, rid: $from_rid, fspath: $from_fspath, intpath: $from_intpath}) "
		   "MERGE (  to_node:FileNode {fqpath: $to_fqpath,   rid: $to_rid,   fspath: $to_fspath,   intpath: $to_intpath})"
		   "MERGE (from_node)-[:Phash4]-(to_node)"
		   ,
				from_fqpath  = from_fqpath,
				from_rid     = from_rid,
				from_fspath  = from_fspath,
				from_intpath = from_intpath,
				to_fqpath    = to_fqpath,
				to_rid       = to_rid,
				to_fspath    = to_fspath,
				to_intpath   = to_intpath,
		   )

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


	def insert_link(self, item1_tup, item2_tup):
		rid_1, fspath_1, intpath_1 = item1_tup
		rid_2, fspath_2, intpath_2 = item2_tup

		itemid_1 = fspath_1 + "/" + intpath_1
		itemid_2 = fspath_2 + "/" + intpath_2
		with self._driver.session() as sess:
			sess.write_transaction(add_phash4_link,
					from_fqpath  = itemid_1,
					from_rid     = rid_1,
					from_fspath  = fspath_1,
					from_intpath = intpath_1,
					to_fqpath    = itemid_2,
					to_rid       = rid_2,
					to_fspath    = fspath_2,
					to_intpath   = intpath_2,
				)


def test():
	ind = GraphApi()

	item1 = (1, "aaaa1", "bbbbb1")
	item2 = (2, "aaaa2", "bbbbb2")
	item3 = (3, "aaaa3", "bbbbb3")
	item4 = (9999999999994, "aaaa4", "bbbbb4")

	ind.insert_link(item1, item2)
	ind.insert_link(item2, item3)
	ind.insert_link(item3, item4)
	ind.insert_link(item4, item1)


if __name__ == "__main__":

	import scanner.logSetup
	scanner.logSetup.initLogging()
	test()

