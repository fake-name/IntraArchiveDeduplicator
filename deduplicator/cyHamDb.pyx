

from libc.stdint cimport uint64_t

# Compute number of bits that are not common between `a` and `b`.
# return value is a plain integer
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

	# Insert phash `nodeHash` into tree, with the associated data `nodeData`
	cpdef insert(self, uint64_t nodeHash, nodeData):

		# If the current node has the same has as the data we're inserting,
		# add the data to the current node's data set
		if nodeHash == self.nodeHash:
			self.nodeData.add(nodeData)
			return

		# otherwise, calculate the edit distance between the new phash and the current node's hash,
		# and either recursively insert the data, or create a new child node for the phash
		distance = hamming(self.nodeHash, nodeHash)
		if not distance in self.children:
			self.children[distance] = BkHammingNode(nodeHash, nodeData)
		else:
			self.children[distance].insert(nodeHash, nodeData)

	# Remove node with hash `nodeHash` and accompanying data `nodeData` from the tree.
	# Returns list of children that must be re-inserted (or false if no children need to be updated),
	# number of nodes deleted, and number of nodes that were moved as a 3-tuple.
	cpdef remove(self, uint64_t nodeHash, nodeData):
		cdef uint64_t deleted = 0
		cdef uint64_t moved = 0

		# If the node we're on matches the hash we want to delete exactly:
		if nodeHash == self.nodeHash:

			# Remove the node data associated with the hash we want to remove
			try:
				self.nodeData.remove(nodeData)
			except KeyError:
				print("ERROR: Key '%s' not in node!" % nodeData)
				print("ERROR: Node keys: '%s'" % self.nodeData)
				raise

			# If we've emptied out the node of data, return all our children so the parent can
			# graft the children into the tree in the appropriate place
			if not self.nodeData:
				# 1 deleted node, 0 moved nodes, return all children for reinsertion by parent
				# Parent will pop this node, and reinsert all it's children where apropriate
				return list(self), 1, 0

			# node has data remaining, do not do any rebuilding
			return False, 1, 0


		selfDist = hamming(self.nodeHash, nodeHash)

		# Removing is basically searching with a distance of zero, and
		# then doing operations on the search result.
		# As such, scan children where the edit distance between `self.nodeHash` and the target `nodeHash` == 0
		# Rebuild children where needed
		if selfDist in self.children:
			moveChildren, childDeleted, childMoved = self.children[selfDist].remove(nodeHash, nodeData)
			deleted += childDeleted
			moved += childMoved

			# If the child returns children, it means the child no longer contains any unique data, so it
			# needs to be deleted. As such, pop it from the tree, and re-insert all it's children as
			# direct decendents of the current node
			if moveChildren:
				self.children.pop(selfDist)
				for childHash, childData in moveChildren:
					self.insert(childHash, childData)
					moved += 1

		return False, deleted, moved

	# Get all child-nodes within an edit distance of `distance` from `baseHash`
	# returns a set containing the data of each matching node, and a integer representing
	# the number of nodes that were touched in the scan.
	# Return value is a 2-tuple
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
	nodes = 0

	def __init__(self):
		pass

	def insert(self, nodeHash, nodeData):

		if not isinstance(nodeData, int):
			raise ValueError("Node data must be an integer row ID")

		if not isinstance(nodeHash, int):
			try:
				nodeHash = int(nodeHash, 2)
			except TypeError:
				raise ValueError("Node hash must be an integer or string encoded binary")



		if not self.root:
			self.root = BkHammingNode(nodeHash, nodeData)
		else:
			self.root.insert(nodeHash, nodeData)


		self.nodes += 1

	def remove(self, nodeHash, nodeData):
		if not self.root:
			raise ValueError("No tree built to remove from!")

		try:
			nodeHash = int(nodeHash, 2)
		except TypeError:
			pass

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

		self.nodes -= deleted

		return deleted, moved

	def getWithinDistance(self, baseHash, distance):
		if not self.root:
			print("WARNING: NO TREE BUILT!")
			return set()


		try:
			baseHash = int(baseHash, 2)
		except TypeError:
			pass

		ret, touched = self.root.getWithinDistance(baseHash, distance)
		# print("Touched %s tree nodes, or %1.3f%%" % (touched, touched/self.nodes * 100))
		# print("Discovered %s match(es)" % len(ret))
		return ret

	def __iter__(self):
		for value in self.root:
			yield value

