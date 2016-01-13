import threading
from contextlib import contextmanager

__author__ = "Mateusz Kobos, Connor Wolf"
#
# Extended to allow blocking/non-blocking and
# context-manager use by Connor Wolf
#
# MIT Licensed. Orignal source:
# https://code.activestate.com/recipes/577803-reader-writer-lock-with-priority-for-writers/

class RWLock:
	"""Synchronization object used in a solution of so-called second
	readers-writers problem. In this problem, many readers can simultaneously
	access a share, and a writer has an exclusive access to this share.
	Additionally, the following constraints should be met:
	1) no reader should be kept waiting if the share is currently opened for
		reading unless a writer is also waiting for the share,
	2) no writer should be kept waiting for the share longer than absolutely
		necessary.

	The implementation is based on [1, secs. 4.2.2, 4.2.6, 4.2.7]
	with a modification -- adding an additional lock (C{self.__readers_queue})
	-- in accordance with [2].

	Sources:
	[1] A.B. Downey: "The little book of semaphores", Version 2.1.5, 2008
	[2] P.J. Courtois, F. Heymans, D.L. Parnas:
		"Concurrent Control with 'Readers' and 'Writers'",
		Communications of the ACM, 1971 (via [3])
	[3] http://en.wikipedia.org/wiki/Readers-writers_problem
	"""

	def __init__(self):
		self.__read_switch = _LightSwitch()
		self.__write_switch = _LightSwitch()
		self.__no_readers = threading.Lock()
		self.__no_writers = threading.Lock()
		self.__readers_queue = threading.Lock()
		"""A lock giving an even higher priority to the writer in certain
		cases (see [2] for a discussion)"""

	def reader_acquire(self, blocking=True):
		self.__readers_queue.acquire(blocking=blocking)
		try:
			self.__no_readers.acquire(blocking=blocking)
			try:
				self.__read_switch.acquire(self.__no_writers, blocking=blocking)
			finally:
				self.__no_readers.release()
		finally:
			self.__readers_queue.release()

	def reader_release(self):
		self.__read_switch.release(self.__no_writers)

	def writer_acquire(self, blocking=True):
		self.__write_switch.acquire(self.__no_readers, blocking=blocking)
		acquired = self.__no_writers.acquire(blocking=blocking)
		if not acquired:
			raise RuntimeError("Failed to acquire no-writers lock. Was this call re-entrant and non-blocking?")


	def writer_release(self):
		self.__no_writers.release()
		self.__write_switch.release(self.__no_readers)

	@contextmanager
	def reader_context(self):
		self.reader_acquire()
		try:
			yield
		finally:
			self.reader_release()

	@contextmanager
	def writer_context(self):
		self.writer_acquire()
		try:
			yield
		finally:
			self.writer_release()

class _LightSwitch:
	"""An auxiliary "light switch"-like object. The first thread turns on the
	"switch", the last one turns it off (see [1, sec. 4.2.2] for details)."""
	def __init__(self):
		self.__counter = 0
		self.__mutex = threading.Lock()

	def acquire(self, lock, blocking=True):
		self.__mutex.acquire(blocking=blocking)
		self.__counter += 1
		if self.__counter == 1:
			lock.acquire()
		self.__mutex.release()

	def release(self, lock):
		self.__mutex.acquire()

		if self.__counter == 0:
			raise RuntimeError("Switch released too many times!")

		self.__counter -= 1
		if self.__counter == 0:
			lock.release()
		self.__mutex.release()
