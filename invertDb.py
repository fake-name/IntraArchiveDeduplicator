

import dbPhashApi

import scanner.logSetup


class TreeInverter(dbPhashApi.PhashDbApi):

	items = {}

	def doLoad(self, silent=False):
		if self.tree.nodes:
			if not silent:
				self.log.error("Tree already built. Reloading will have no effect!")
				raise ValueError
			return

		cur = self.getStreamingCursor(wantCols=['dbId', 'itemHash', 'pHash', 'fsPath', 'internalPath'], where=(self.table.phash != None))
		loaded = 0

		rows = cur.fetchmany(self.streamChunkSize)
		while rows:
			for dbId, itemHash, pHash, fsPath, internalPath in rows:
				if not fsPath in self.items:
					self.items[fsPath] = set()

				self.items[fsPath].add((dbId, itemHash, pHash, internalPath))

				if pHash != None:
					self.tree.unlocked_insert(pHash, dbId)

			loaded += len(rows)
			self.log.info("Loaded %s phash data sets.", loaded)
			rows = cur.fetchmany(self.streamChunkSize)

		cur.close()

	def dumpFileStats(self):
		self.log.info("Unique files found: %s", len(self.items))

	def buildInvertedTree(self):
		inv_tree = []
		self.log.info("Building inverted tree!")

		for key, value in self.items.items():
			if any([tmp[2] for tmp in value]):
				inv_tree.append((len(value), key, value))
		inv_tree.sort()

		self.log.info("Tree sorted!")

		for item_cnt, path, contents in inv_tree:
			print(item_cnt, path)




def go():
	inv = TreeInverter()
	print(inv)
	inv.dumpFileStats()
	inv.buildInvertedTree()



if __name__ == '__main__':
	scanner.logSetup.initLogging()
	go()

