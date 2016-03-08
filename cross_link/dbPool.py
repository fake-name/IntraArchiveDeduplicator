
import psycopg2.pool
import settings

class ConnectionPool():
	_shared_state = {}

	_db_max_connections = 50

	def __init__(self):
		self.__dict__ = self._shared_state

		if not hasattr(self, 'connected'):
			print("Database connection pool init!")
			try:
				self.dbPool = psycopg2.pool.ThreadedConnectionPool(1, self._db_max_connections, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
			except psycopg2.OperationalError:
				self.dbPool = psycopg2.pool.ThreadedConnectionPool(1, self._db_max_connections, host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

			self.connected = True

	def getconn(self):
		return self.dbPool.getconn()

	def putconn(self, conn):
		self.dbPool.putconn(conn)


pool = ConnectionPool()
