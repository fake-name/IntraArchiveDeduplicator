
import scanner.logSetup
scanner.logSetup.initLogging()


import cross_link.processDownload
import dbPhashApi
from concurrent.futures import ThreadPoolExecutor


import deduplicator.ProcessArchive

class TreeInverter(dbPhashApi.PhashDbApi):

	items = {}

	def __init__(self, *args, **kwargs):
		print("Initializing")
		super().__init__(*args, **kwargs)
		print("Initialized?")

		self.mp = cross_link.processDownload.MangaProcessor()
		self.hp = cross_link.processDownload.HentaiProcessor()

	def doLoad(self, silent=False):
		if self.tree.nodes:
			if not silent:
				self.log.error("Tree already built. Reloading will have no effect!")
				raise ValueError
			return

		cur = self.getStreamingCursor(wantCols=['dbId', 'itemHash', 'pHash', 'fsPath', 'internalPath', 'imgx', 'imgy'], where=(self.table.phash != None))
		loaded = 0

		rows = cur.fetchmany(self.streamChunkSize)
		while rows:
			for dbId, itemHash, pHash, fsPath, internalPath, imgx, imgy in rows:
				if not (imgx and imgy):
					continue
				if not fsPath in self.items:
					self.items[fsPath] = set()

				self.items[fsPath].add((dbId, itemHash, pHash, internalPath))

				if pHash != None:
					self.tree.unlocked_insert(pHash, dbId)

			loaded += len(rows)
			self.log.info("Loaded %s phash data sets.", loaded)
			rows = cur.fetchmany(self.streamChunkSize)

			# if loaded > 1000000:
			# 	break

		cur.close()

	def dumpFileStats(self):
		self.log.info("Unique files found: %s", len(self.items))

	def process_item(self, item_cnt, path, contents):
		if item_cnt < 2:
			return

		status, bestMatch, common = deduplicator.ProcessArchive.processDownload(filePath=path)
		self.log.info("Results for archive: '{}' - '{}'".format(path, bestMatch))
		# deduplicator.ProcessArchive.processDownload(*args, **kwargs)

		if status:
			delItem, dupItem = path, bestMatch
			self.mp.crossLink(delItem, dupItem)
			self.hp.crossLink(delItem, dupItem)
			print(item_cnt, path, bestMatch)

	def buildInvertedTree(self):

		inv_tree = []
		self.log.info("Building inverted tree!")

		for key, value in self.items.items():
			if any([tmp[2] for tmp in value]):
				inv_tree.append((len(value), key, value))
		inv_tree.sort()

		self.log.info("Tree sorted!")


		with ThreadPoolExecutor(max_workers=1) as executor:
			self.log.info("Submitting items to executor")
			for item_cnt, path, contents in inv_tree:
				executor.submit(self.process_item, item_cnt, path, contents)
			self.log.info("All items in processing queue. Waiting for pending jobs to complete.")








def go():
	inv = TreeInverter()
	print(inv)
	inv.dumpFileStats()
	inv.buildInvertedTree()



if __name__ == '__main__':
	go()

