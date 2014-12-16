
import scanner.hashFile as hf
import UniversalArchiveInterface
import magic

class PhashArchive(UniversalArchiveInterface.ArchiveReader):
	'''
	Encapsulates and caches the mechanics needed to scan an archive and
	phash it's contents.
	'''
	# Have to override the __init__ so we can properly empty the self.hashedFiles dict.
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.hashedFiles = {}

	def iterHashes(self):
		'''
		Iterate over all the files in the archive, and yield 2-tuples
		containing the internal-path and the internal-item-data as a dict
		'''
		items = list(self.getFileList())
		items.sort()
		for item in items:
			if item not in self.hashedFiles:
				fp = self.open(item)
				cont = fp.read()
				ret = hf.getHashDict(item, cont)
				ret['cont'] = cont
				ret['type'] = magic.from_buffer(cont)
				self.hashedFiles[item] = ret
			yield item, self.hashedFiles[item]


	def getHashInfo(self, intPath):
		'''
		Get the info-dict for internal item `intPath`
		'''
		if intPath not in self.hashedFiles:
			fp = self.open(intPath)
			cont = fp.read()
			ret = hf.getHashDict(intPath, cont)
			ret['cont'] = cont
			ret['type'] = magic.from_buffer(cont)
			self.hashedFiles[intPath] = ret

		return self.hashedFiles[intPath]
