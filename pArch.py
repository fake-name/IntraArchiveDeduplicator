
import scanner.hashFile as hf
import UniversalArchiveInterface
import magic

def fix_mime(mtype):

	# So some versions of libmagic return application/CDFV2-corrupt for some
	# thumbs.db, while some return application/CDFV2 for the /same/ file.
	# In any event, I've never seen a application/CDFV2 file that wasn't
	# one of the garbage application/CDFV2 file, so just pretend
	# the corrupt ones aren't corrupt, since we don't wany any of them
	# anyways.
	if mtype == "application/CDFV2-corrupt":
		mtype = 'application/CDFV2'
	return mtype

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
				ret['type'] = fix_mime(magic.from_buffer(cont, mime=True))
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
			ret['type'] = fix_mime(magic.from_buffer(cont, mime=True))
			self.hashedFiles[intPath] = ret

		return self.hashedFiles[intPath]
