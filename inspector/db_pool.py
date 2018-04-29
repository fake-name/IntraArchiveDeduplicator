
import contextlib
import psycopg2
import psycopg2.pool

import settings
# from guess_language import guess_language

__cpool = psycopg2.pool.ThreadedConnectionPool(
							minconn  = 2,
							maxconn  = 5,
							dbname   = settings.PSQL_DB_NAME,
							host     = settings.PSQL_IP,
							password = settings.PSQL_PASS,
							user     = settings.PSQL_USER,
	)

@contextlib.contextmanager
def db_cursor(key=None):
	try:
		with __cpool.getconn(key) as conn, conn.cursor() as cur:
			yield cur
	finally:
		__cpool.putconn(conn, key)