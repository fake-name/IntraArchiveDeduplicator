

from libc.stdint cimport uint64_t
from libc.stdint cimport int64_t


from libcpp.pair cimport pair as cpair
# from libcpp.tuple cimport tuple
from libcpp.deque cimport deque
from libcpp.vector cimport vector

# TODO: Convert sets to cset v
from libcpp.set cimport set as cset
from contextlib import contextmanager
# import traceback

import errno
import gc
import os

cdef extern from "./deduplicator/bktree.hpp" namespace "BK_Tree_Ns":
	# ctypedef cset[int64_t] set_64
	ctypedef cpair[cset[int64_t], int64_t] search_ret
	# ctypedef tuple[bool, int64_t, int64_t] rebuild_ret
	ctypedef cpair[int64_t, int64_t] hash_pair
	ctypedef deque[hash_pair] return_deque

	cdef int64_t f_hamming(int64_t a, int64_t b)

	cdef cppclass BK_Tree:
		BK_Tree() except +
		void            insert(int64_t nodeHash, int64_t nodeData) nogil
		void            unlocked_insert(int64_t nodeHash, int64_t nodeData) nogil
		vector[int64_t] remove(int64_t nodeHash, int64_t nodeData) nogil
		search_ret      getWithinDistance(int64_t baseHash, int distance) nogil
		search_ret      unlocked_getWithinDistance(int64_t baseHash, int distance) nogil
		int            get_read_lock()      nogil
		int            get_write_lock()     nogil
		int            try_get_read_lock()  nogil
		int            try_get_write_lock() nogil
		int            free_read_lock()     nogil
		int            free_write_lock()    nogil
		int            clear_tree()         nogil
		return_deque   get_all()            nogil


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



# Most of these calls can release the GIL, because they only manipulate the BK_Tree internal data structure.
cdef class CPP_BkHammingTree(object):
	cdef BK_Tree *treeroot_p

	def __init__(self):
		self.treeroot_p = new BK_Tree()

	cpdef insert(self, int64_t nodeHash, int64_t nodeData):
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			root_ptr.insert(nodeHash, nodeData)

	cpdef unlocked_insert(self, int64_t nodeHash, int64_t nodeData):
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			root_ptr.unlocked_insert(nodeHash, nodeData)

	cpdef remove(self, int64_t nodeHash, int64_t nodeData):
		cdef vector[int64_t] ret
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			ret = root_ptr.remove(nodeHash, nodeData)
		return ret[0], ret[1]

	cpdef getWithinDistance(self, int64_t baseHash, int distance):
		cdef search_ret have
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			have = root_ptr.getWithinDistance(baseHash, distance)
		had = set(have.first)
		touched = int(have.second)

		return had, touched

	cpdef unlocked_getWithinDistance(self, int64_t baseHash, int distance):
		cdef search_ret have
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			have = root_ptr.unlocked_getWithinDistance(baseHash, distance)
		had = set(have.first)
		touched = int(have.second)

		return had, touched


	# Wrap the lock calls.
	cpdef try_get_read_lock(self):
		print("Calling try_get_read_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.try_get_read_lock()
		print("try_get_read_lock return val: {}".format(retval))
		if retval == 0:
			return True
		if retval == errno.EBUSY:
			return False
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (try_get_read_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (try_get_read_lock): {}".format(retval))


	cpdef try_get_write_lock(self):
		print("Calling try_get_write_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.try_get_write_lock()
		print("try_get_write_lock return val: {}".format(retval))
		if retval == 0:
			return True
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (try_get_write_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (try_get_write_lock): {}".format(retval))


	cpdef get_read_lock(self):
		print("Calling get_read_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.get_read_lock()
		print("get_read_lock return val: {}".format(retval))
		if retval == 0:
			return
		if retval == errno.EBUSY:
			return False
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (get_read_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (get_read_lock): {}".format(retval))


	cpdef get_write_lock(self):
		print("Calling get_write_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.get_write_lock()
		print("get_write_lock return val: {}".format(retval))
		if retval == 0:
			return
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (get_write_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (get_write_lock): {}".format(retval))


	cpdef free_read_lock(self):
		print("Calling free_read_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.free_read_lock()
		print("free_read_lock return val: {}".format(retval))
		if retval == 0:
			return
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (free_read_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (free_read_lock): {}".format(retval))


	cpdef free_write_lock(self):
		print("Calling free_write_lock from thread: {}".format(os.getpid()))
		retval = self.treeroot_p.free_write_lock()
		print("free_write_lock return val: {}".format(retval))
		if retval == 0:
			return
		if retval in errno.errorcode:
			raise RuntimeError("Exception in lock management (free_write_lock): {}".format(errno.errorcode[retval]))
		else:
			raise RuntimeError("Unknown Exception in lock management (free_write_lock): {}".format(retval))


	cpdef get_all(self):
		cdef return_deque ret
		cdef BK_Tree *root_ptr = self.treeroot_p
		with nogil:
			ret = root_ptr.get_all()
		extracted = []
		deq_sz = ret.size()
		for x in range(deq_sz):
			if ret[x].first != 0 or ret[x].second != 0:
				extracted.append((ret[x].first, ret[x].second))
		return extracted

	cpdef clear_tree(self):
		ret = self.treeroot_p.clear_tree()
		print("Tree cleared!")
		return ret


	def __dealloc__(self):
		del self.treeroot_p


class CPPBkHammingTree(object):

	def __init__(self):
		cur             = threading.current_thread().name
		self.log        = logging.getLogger("Main.Tree."+cur)
		self.root       = CPP_BkHammingTree()
		# self.updateLock = CPPLockProxy(self.root)
		self.nodes = 0



	def insert(self, nodeHash, nodeData):
		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))
		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		self.root.insert(nodeHash, nodeData)
		self.nodes += 1

	def unlocked_insert(self, nodeHash, nodeData):


		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))
		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		# print("Root: ", self.root)
		self.root.unlocked_insert(nodeHash, nodeData)

		self.nodes += 1


	def remove(self, nodeHash, nodeData):

		if not isinstance(nodeData, int):
			raise ValueError("Data must be an integer! Passed value '%s', type '%s'" % (nodeData, type(nodeData)))

		if not isinstance(nodeHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (nodeHash, type(nodeHash)))

		if self.nodes == 0:
			raise ValueError("Remove from empty tree!")

		deleted, moved = self.root.remove(nodeHash, nodeData)
		# Moved seems to always be 0
		self.log.info("Deletion operation removed %s item(s)", deleted)
		return deleted, moved

	def getWithinDistance(self, baseHash, distance):

		# print("Search for %s within distance of %s" % (baseHash, distance))
		if not isinstance(baseHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (baseHash, type(baseHash)))

		if self.nodes == 0:
			raise ValueError("Search on empty tree!")


		ret, touched = self.root.getWithinDistance(baseHash, distance)
		percent = (touched/self.nodes) * 100
		self.log.info("Search for '%s', distance '%s', Touched %s tree nodes, or %1.3f%%. Discovered %s match(es)" % (baseHash, distance, touched, percent, len(ret)))

		return ret

	def unlocked_getWithinDistance(self, baseHash, distance):

		# print("Search for %s within distance of %s" % (baseHash, distance))
		if not isinstance(baseHash, int):
			raise ValueError("Hashes must be an integer! Passed value '%s', type '%s'" % (baseHash, type(baseHash)))

		if self.nodes == 0:
			raise ValueError("Search on empty tree!")


		ret, touched = self.root.unlocked_getWithinDistance(baseHash, distance)
		percent = (touched/self.nodes) * 100
		self.log.info("Search for '%s', distance '%s', Touched %s tree nodes, or %1.3f%%. Discovered %s match(es)" % (baseHash, distance, touched, percent, len(ret)))

		return ret

	# Explicitly dump all the tree items.
	# Note: Only ever called from within a lock-synchronized context.
	def dropTree(self):

		cleared = self.root.clear_tree()
		self.nodes  = 0

		self.log.info("Tree-Drop deleted %s items", cleared)
		collected = gc.collect()
		self.log.info("GC collected %s items.", collected)

		assert self.root is not None


	def get_read_lock(self, blocking=True):
		if blocking:
			self.root.get_read_lock()
		else:
			self.root.try_get_read_lock()


	def free_read_lock(self):
		self.root.free_read_lock()

	def get_write_lock(self, blocking=True):
		if blocking:
			self.root.get_write_lock()
		else:
			self.root.try_get_write_lock()


	def free_write_lock(self):
		self.root.free_write_lock()



	@contextmanager
	def reader_context(self):
		self.root.get_read_lock()
		try:
			yield
		finally:
			self.root.free_read_lock()

	@contextmanager
	def writer_context(self):
		self.root.get_write_lock()
		try:
			yield
		finally:
			self.root.free_write_lock()


	def __iter__(self):
		with self.reader_context():
			for value in self.root.get_all():
				yield value

	def __setattr__(self, name, value):
		if name == "root":
			assert value != None, "Attempting to set key '{}' to value '{}'".format(name, value)

		object.__setattr__(self, name, value)


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
import logging

BkHammingTree = CPPBkHammingTree

