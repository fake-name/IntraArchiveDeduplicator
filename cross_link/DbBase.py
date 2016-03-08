
import traceback
import psycopg2
import abc
import settings
import logging
from contextlib import contextmanager

from . import DbRoot as dbb

# Absolutely minimal class to handle opening a DB interface.


class DbBase(dbb.TransactionMixin, metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def loggerPath(self):
		return None

	def __init__(self):
		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Base DB Interface Starting!")

	def openDB(self):
		self.log.info("Opening DB...",)

		# First try local socket connection, fall back to a IP-based connection.
		# That way, if the server is local, we get the better performance of a local socket.
		try:
			self.conn = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		except psycopg2.OperationalError:
			self.conn = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

		# self.conn = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
		# self.conn.autocommit = True
		self.log.info("DB opened.")

	def closeDB(self):
		self.log.info("Closing DB...",)
		self.conn.close()
		self.log.info("DB Closed")

	def get_cursor(self):
		return self.conn.cursor()


	def release_cursor(self, cursor):
		return None
