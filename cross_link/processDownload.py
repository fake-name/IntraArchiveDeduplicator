

import os.path
from . import RetreivalDbBase


class DownloadProcessor(RetreivalDbBase.ScraperDbBase):

	pluginName = 'Download Processor'

	loggerPath = 'Main.DlProc'
	tableKey = 'n/a'



	def crossLink(self, delItem, dupItem, isPhash=False):
		self.log.warning("Duplicate found! Cross-referencing file")

		delItemRoot, delItemFile = os.path.split(delItem)
		dupItemRoot, dupItemFile = os.path.split(dupItem)
		self.log.info("Remove:	'%s', '%s'", delItemRoot, delItemFile)
		self.log.info("Match: 	'%s', '%s'", dupItemRoot, dupItemFile)

		srcRow = self.getRowsByValue(limitByKey=False, downloadpath=delItemRoot, filename=delItemFile)
		dstRow = self.getRowsByValue(limitByKey=False, downloadpath=dupItemRoot, filename=dupItemFile)

		# print("HaveItem", srcRow)
		if srcRow and len(srcRow) == 1:
			srcId = srcRow[0]['dbId']
			self.log.info("Relinking!")
			self.updateDbEntryById(srcId, filename=dupItemFile, downloadpath=dupItemRoot)

			if isPhash:
				tags = 'deleted was-duplicate phash-duplicate'
			else:
				tags = 'deleted was-duplicate'

			self.addTags(dbId=srcId, tags=tags, limitByKey=False)

			# Allow for situations where we're linking to something that already has other links
			if dstRow:

				dstId = dstRow[0]['dbId']
				self.addTags(dbId=srcId, tags='crosslink-{dbId}'.format(dbId=dstId), limitByKey=False)
				self.addTags(dbId=dstId, tags='crosslink-{dbId}'.format(dbId=dstId), limitByKey=False)
				self.log.info("Found destination row. Cross-linking!")
				return

		self.log.warn("Cross-referencing file failed!")
		self.log.warn("Remove:	'%s', '%s'", delItemRoot, delItemFile)
		self.log.warn("Match: 	'%s', '%s'", dupItemRoot, dupItemFile)
		self.log.warn("SrcRow:	'%s'", srcRow)
		self.log.warn("DstRow:	'%s'", dstRow)



# Subclasses to specify the right table names
class MangaProcessor(DownloadProcessor):
	tableName = 'MangaItems'
	pron = False

class HentaiProcessor(DownloadProcessor):
	tableName = 'HentaiItems'
	pron = True

