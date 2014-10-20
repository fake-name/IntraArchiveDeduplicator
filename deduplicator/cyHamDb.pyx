

from libc.stdint cimport uint64_t

cdef uint64_t hamming(uint64_t a, uint64_t b):

	cdef uint64_t x
	cdef int tot

	tot = 0

	x = (a ^ b)
	while x > 0:
		tot += x & 1
		x >>= 1
	return tot

cdef class BkHammingNode(object):

	cdef uint64_t nodeHash
	cdef set nodeData
	cdef dict children

	def __init__(self, nodeHash, nodeData):
		self.nodeData = set((nodeData, ))
		self.children = {}
		self.nodeHash = nodeHash

	cpdef insert(self, uint64_t nodeHash, nodeData):
		if nodeHash == self.nodeHash:
			self.nodeData.add(nodeData)
			return

		distance = hamming(self.nodeHash, nodeHash)
		if not distance in self.children:
			self.children[distance] = BkHammingNode(nodeHash, nodeData)
		else:
			self.children[distance].insert(nodeHash, nodeData)

	cpdef remove(self, uint64_t nodeHash, nodeData):
		cdef uint64_t deleted = 0
		cdef uint64_t moved = 0

		if nodeHash == self.nodeHash:
			self.nodeData.remove(nodeData)
			# If we've emptied out the node of data, return all our children so the parent can
			# graft the children into the tree in the appropriate place

			if not self.nodeData:
				return list(self), 1, 0
			return [], 1, 0


		selfDist = hamming(self.nodeHash, nodeHash)

		# Removing is basically searching with a distance of zero, and
		# then doing operations on the search result.


		if selfDist in self.children:
			moveChildren, childDeleted, childMoved = self.children[selfDist].remove(nodeHash, nodeData)
			deleted += childDeleted
			moved += childMoved

			if moveChildren:
				self.children.pop(selfDist)
				for childHash, childData in moveChildren:
					self.insert(childHash, childData)
					moved += 1

		return [], deleted, moved


	cpdef getWithinDistance(self, uint64_t baseHash, int distance):
		cdef uint64_t selfDist

		selfDist = hamming(self.nodeHash, baseHash)

		ret = set()

		if selfDist <= distance:
			ret |= set(self.nodeData)

		touched = 1

		for key in self.children.keys():

			if key <= selfDist+distance and key >= selfDist-distance:

				new, tmpTouch = self.children[key].getWithinDistance(baseHash, distance)
				touched += tmpTouch
				ret |= new

		return ret, touched

	def __iter__(self):
		for child in self.children.values():
			for item in child:
				yield item
		for item in self.nodeData:
			yield (self.nodeHash, item)

class BkHammingTree(object):
	root = None

	def __init__(self):
		self.nodes = 0

	def insert(self, nodeHash, nodeData):
		if not self.root:
			self.root = BkHammingNode(nodeHash, nodeData)
		else:
			self.root.insert(nodeHash, nodeData)


		self.nodes += 1

	def remove(self, nodeHash, nodeData):
		if not self.root:
			raise ValueError("No tree built to remove from!")

		rootless, deleted, moved = self.root.remove(nodeHash, nodeData)

		# If the node we're deleting is the root node, we need to handle it properly
		# if it is, overwrite the root node with one of the values returned, and then
		# rebuild the entire tree by reinserting all the nodes
		if rootless:
			print("Tree root deleted! Rebuilding...")
			rootHash, rootData = rootless.pop()
			self.root = BkHammingNode(rootHash, rootData)
			for childHash, childData in rootless:
				self.root.insert(childHash, childData)



		return deleted, moved

	def getWithinDistance(self, baseHash, distance):
		if not self.root:
			return set()

		ret, touched = self.root.getWithinDistance(baseHash, distance)
		print("Touched %s tree nodes, or %1.3f%%" % (touched, touched/self.nodes * 100))
		print("Discovered %s match(es)" % len(ret))
		return ret

	def __iter__(self):
		for value in self.root:
			yield value

