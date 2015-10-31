

from libc.stdint cimport uint64_t
from libc.stdint cimport int64_t


from libcpp.pair cimport pair as cpair
# from libcpp.tuple cimport tuple
from libcpp.deque cimport deque
from libcpp.vector cimport vector

# TODO: Convert sets to cset v
from libcpp.set cimport set as cset
from contextlib import contextmanager

cdef extern from "./deduplicator/bktree.hpp" namespace "bk_tree":
	# ctypedef cset[int64_t] set_64
	ctypedef cpair[cset[int64_t], int64_t] search_ret
	# ctypedef tuple[bool, int64_t, int64_t] rebuild_ret
	ctypedef cpair[int64_t, int64_t] hash_pair
	ctypedef deque[hash_pair] return_deque

	cdef int64_t f_hamming(int64_t a, int64_t b)

	cdef cppclass BK_Tree:
		BK_Tree(int64_t, int64_t) except +
		void            insert(int64_t nodeHash, int64_t nodeData)
		void            unlocked_insert(int64_t nodeHash, int64_t nodeData)
		vector[int64_t] remove(int64_t nodeHash, int64_t nodeData)
		search_ret      getWithinDistance(int64_t baseHash, int distance)
		void            get_read_lock()
		void            get_write_lock()
		void            free_read_lock()
		void            free_write_lock()




cdef int64_t hamming(int64_t a, int64_t b):
	'''
	Compute number of bits that are not common between `a` and `b`.
	return value is a plain integer
	'''

	cdef int tot
	tot = 0

	# Messy explicit casting to work around the fact that
	# >> on a signed number is arithmetic, rather then logical,
	# which means that >> on -1 results in -1 (it shifts in the sign
	# value). This was breaking comparisons since we're checking if
	# x > 0 (it could be negative if the numbers are signed.)

	a = <uint64_t>a
	b = <uint64_t>b

	cdef uint64_t x
	x = (a ^ b)

	while x > 0:
		tot += x & 1
		x >>= 1
	return tot




cdef class CPP_BkHammingTree(object):
	cdef BK_Tree *treeroot_p

	def __init__(self, int64_t nodeHash, int64_t nodeData):
		self.treeroot_p = new BK_Tree(nodeHash, nodeData)

	cpdef insert(self, int64_t nodeHash, int64_t nodeData):
		self.treeroot_p.insert(nodeHash, nodeData)

	cpdef unlocked_insert(self, int64_t nodeHash, int64_t nodeData):
		self.treeroot_p.unlocked_insert(nodeHash, nodeData)

	cpdef remove(self, int64_t nodeHash, int64_t nodeData):
		cdef vector[int64_t] ret = self.treeroot_p.remove(nodeHash, nodeData)
		return ret[0], ret[1]

	cpdef getWithinDistance(self, int64_t baseHash, int distance):

		cdef search_ret have = self.treeroot_p.getWithinDistance(baseHash, distance)

		had = set(have.first)
		touched = int(have.second)

		return had, touched

	# Wrap the lock calls.
	cpdef get_read_lock(self):
		self.treeroot_p.get_read_lock()
	cpdef get_write_lock(self):
		self.treeroot_p.get_write_lock()
	cpdef free_read_lock(self):
		self.treeroot_p.free_read_lock()
	cpdef free_write_lock(self):
		self.treeroot_p.free_write_lock()

	# def __iter__(self):
	# 	for child in self.children.values():
	# 		for item in child:
	# 			yield item
	# 	for item in self.nodeData:
	# 		yield (self.nodeHash, item)


	def __dealloc__(self):
		del self.treeroot_p



cdef class BkHammingNode(object):

	cdef int64_t nodeHash
	cdef set nodeData
	cdef dict children

	def __init__(self, int64_t nodeHash, int64_t nodeData):
		self.nodeData = {nodeData}
		self.children = {}
		self.nodeHash = nodeHash

	cpdef insert(self, int64_t nodeHash, int64_t nodeData):
		'''
		Insert phash `nodeHash` into tree, with the associated data `nodeData`
		'''

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

	cpdef remove(self, int64_t nodeHash, int64_t nodeData):
		'''
		Remove node with hash `nodeHash` and accompanying data `nodeData` from the tree.
		Returns list of children that must be re-inserted (or false if no children need to be updated),
		number of nodes deleted, and number of nodes that were moved as a 3-tuple.
		'''

		cdef int64_t deleted = 0
		cdef int64_t moved = 0

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

	cpdef getWithinDistance(self, int64_t baseHash, int distance):
		'''
		Get all child-nodes within an edit distance of `distance` from `baseHash`
		returns a set containing the data of each matching node, and a integer representing
		the number of nodes that were touched in the scan.
		Return value is a 2-tuple
		'''

		cdef int64_t selfDist

		cdef int postDelta
		cdef int negDelta

		selfDist = hamming(self.nodeHash, baseHash)

		ret = set()

		if selfDist <= distance:
			ret = set(self.nodeData)

		touched = 1


		for key in self.children:

			# need to use signed intermediate values to avoid wrap-around issues
			# when the value of `selfDist` < the value of `distance`, negDelta would
			# wrap if if were unsigned, leading to a false-negative comparison.
			postDelta = selfDist + distance
			negDelta  = selfDist - distance

			if key <= postDelta and key >= negDelta:
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


# Expose the casting behaviour because I need to be
# able to verify it's doing what it's supposed to.
cdef uint64_t cExplicitUnsignCast(int64_t inVal):
	cdef uint64_t a
	a = <uint64_t>inVal
	return a

cdef int64_t cExplicitSignCast(uint64_t inVal):
	cdef int64_t a
	a = <int64_t>inVal
	return a

def explicitUnsignCast(inVal):
	return cExplicitUnsignCast(inVal)

def explicitSignCast(inVal):
	return cExplicitSignCast(inVal)

# Expose the hamming distance calculation
# so I can test it with the unit tests.
def hamming_dist(a, b):
	return hamming(a, b)

def f_hamming_dist(a, b):
	return f_hamming(a, b)


import threading
import rwlock
import logging



class PyBkHammingTree(object):
	root = None
	nodes = 0

	def __init__(self):
		self.updateLock = rwlock.RWLock()
		cur = threading.current_thread().name
		self.log = logging.getLogger("Main.Tree."+cur)
		pass

	# TODO: Right now, this blindly increments the number of `self.nodes`
	# on every call. This means if you insert the /same/ item repeatedly,
	# it'll increase the value of `self.nodes`, despite not making any
	# actual changes to the tree. Fix this, maybe?
	def unlocked_insert(self, nodeHash, nodeData):

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))

		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))


		if not self.root:
			self.root = BkHammingNode(nodeHash, nodeData)
		else:
			self.root.insert(nodeHash, nodeData)
		self.nodes += 1

	def insert(self, nodeHash, nodeData):

		with self.updateLock.writer_context():
			self.unlocked_insert(nodeHash, nodeData)

	def remove(self, nodeHash, nodeData):
		if not self.root:
			raise ValueError("No tree built to remove from!")

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))

		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		with self.updateLock.writer_context():
			rootless, deleted, moved = self.root.remove(nodeHash, nodeData)

			# If the node we're deleting is the root node, we need to handle it properly
			# if it is, overwrite the root node with one of the values returned, and then
			# rebuild the entire tree by reinserting all the nodes
			if rootless:
				self.log.info("Tree root deleted! Rebuilding...")
				rootHash, rootData = rootless.pop()
				self.root = BkHammingNode(rootHash, rootData)
				for childHash, childData in rootless:
					self.root.insert(childHash, childData)

			self.nodes -= deleted

		return deleted, moved

	def getWithinDistance(self, baseHash, distance):

		if not isinstance(baseHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (baseHash, type(baseHash)))

		with self.updateLock.reader_context():
			if not self.root:
				self.log.info("WARNING: NO TREE BUILT!")
				return set()

			ret, touched = self.root.getWithinDistance(baseHash, distance)
			self.log.info("Search for '%s', distance '%s', Touched %s tree nodes, or %1.3f%%. Discovered %s match(es)" % (baseHash, distance, touched, touched/self.nodes * 100, len(ret)))

		return ret

	# Explicitly dump all the tree items.
	# Note: Only ever called from within a lock-synchronized context.
	def dropTree(self):
		self.root = None
		self.nodes = 0

	def __iter__(self):
		for value in self.root:
			yield value


class CPPLockProxy(object):
	def __init__(self, treehandle):
		self.tree = treehandle

	@contextmanager
	def reader_context(self):
		self.tree.get_read_lock()
		try:
			yield
		finally:
			self.tree.free_read_lock()

	@contextmanager
	def writer_context(self):
		self.tree.get_write_lock()
		try:
			yield
		finally:
			self.tree.free_write_lock()


class CPPBkHammingTree(object):
	root = None
	nodes = 0

	def __init__(self):
		cur             = threading.current_thread().name
		self.log        = logging.getLogger("Main.Tree."+cur)
		self.root       = CPP_BkHammingTree(0, 0)
		self.updateLock = CPPLockProxy(self.root)

	def insert(self, nodeHash, nodeData):
		assert(self.root)

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))
		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		self.root.insert(nodeHash, nodeData)
		self.nodes += 1

	def unlocked_insert(self, nodeHash, nodeData):
		assert(self.root)

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))
		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		self.root.unlocked_insert(nodeHash, nodeData)
		self.nodes += 1


	def remove(self, nodeHash, nodeData):
		if not self.root:
			raise ValueError("No tree built to remove from!")

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))

		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))


		rootless, deleted, moved = self.root.remove(nodeHash, nodeData)

		return deleted, moved

	def getWithinDistance(self, baseHash, distance):
		assert(self.root)

		if not isinstance(baseHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (baseHash, type(baseHash)))

		ret, touched = self.root.getWithinDistance(baseHash, distance)
		self.log.info("Search for '%s', distance '%s', Touched %s tree nodes, or %1.3f%%. Discovered %s match(es)" % (baseHash, distance, touched, touched/self.nodes * 100, len(ret)))

		return ret

	# Explicitly dump all the tree items.
	# Note: Only ever called from within a lock-synchronized context.
	def dropTree(self):
		self.root = None
		self.nodes = 0
		self.root       = CPP_BkHammingTree(0, 0)
		self.updateLock = CPPLockProxy(self.root)



	# def __iter__(self):
	# 	for value in self.root:
	# 		yield value


BkHammingTree = PyBkHammingTree
# BkHammingTree = CPPBkHammingTree