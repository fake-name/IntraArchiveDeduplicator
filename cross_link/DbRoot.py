
import traceback
import abc
from contextlib import contextmanager
from . import LogBase
import threading
from . import dbPool
import traceback

class TransactionMixin(object, metaclass=abc.ABCMeta):

	@contextmanager
	def transaction(self, commit=True):
		cursor = self.get_cursor()
		if commit:
			cursor.execute("BEGIN;")

		try:
			yield cursor

		except Exception as e:
			self.log.error("Error in transaction!")
			for line in traceback.format_exc().split("\n"):
				self.log.error(line)
			if commit:
				self.log.warn("Rolling back.")
				cursor.execute("ROLLBACK;")
			else:
				self.log.warn("NOT Rolling back.")

			raise e

		finally:
			if commit:
				cursor.execute("COMMIT;")
			self.release_cursor(cursor)


	@abc.abstractmethod
	def get_cursor(self):
		return None

	@abc.abstractmethod
	def release_cursor(self, cursor):
		return None



# Minimal class to handle opening a DB interface.
class DbBase(LogBase.LoggerMixin, TransactionMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def loggerPath(self):
		return None

	def __init__(self):
		super().__init__()
		self.connections = {}

	def __del__(self):
		if hasattr(self, 'connections'):
			for conn in self.connections:
				dbPool.pool.putconn(conn)

	@property
	def __thread_cursor(self):
		'''
		__getCursor and __freeConn rely on "magic" thread ID cookies to associate
		threads with their correct db pool interfaces
		'''

		tid = threading.get_ident()

		if tid in self.connections:
			self.log.critical('Recursive access to singleton thread-specific resource!')
			self.log.critical("Calling thread ID: '%s'", tid)
			self.log.critical("Allocated handles")
			for key, value in self.connections.items():
				self.log.critical("	'%s', '%s'", key, value)

			raise ValueError("Recursive cursor retreival! What's going on?")

		self.connections[tid] = dbPool.pool.getconn()
		return self.connections[tid].cursor()

	def __freeConn(self):
		conn = self.connections.pop(threading.get_ident())
		dbPool.pool.putconn(conn)

	def get_cursor(self):
		return self.__thread_cursor

	def release_cursor(self, cursor):
		self.__freeConn()