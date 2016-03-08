
if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False

import logging
import psycopg2
import functools
import operator as opclass
import abc

import threading
import settings
import os
import traceback

from . import nameTools as nt
nt.dirNameProxy.startDirObservers(useObservers=False)

from . import DbBase

import sql
import time
import sql.operators as sqlo

from contextlib import contextmanager

@contextmanager
def transaction(cursor, commit=True):
	if commit:
		cursor.execute("BEGIN;")

	try:
		yield

	except Exception as e:
		if commit:
			cursor.execute("ROLLBACK;")
		raise e

	finally:
		if commit:
			cursor.execute("COMMIT;")



class ScraperDbBase(DbBase.DbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	shouldCanonize = True

	loggers = {}
	dbConnections = {}

	# Turn on to print all db queries to STDOUT before running them.
	# Intended for debugging DB interactions.
	# Excessively verbose otherwise.
	QUERY_DEBUG = False

	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None


	@abc.abstractmethod
	def tableKey(self):
		return None

	@abc.abstractmethod
	def tableName(self):
		return None


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Messy hack to do log indirection so I can inject thread info into log statements, and give each thread it's own DB handle.
	# Basically, intercept all class member accesses, and if the access is to either the logging interface, or the DB,
	# look up/create a per-thread instance of each, and return that
	#
	# The end result is each thread just uses `self.conn` and `self.log` as normal, but actually get a instance of each that is
	# specifically allocated for just that thread
	#
	# ~~Sqlite 3 doesn't like having it's DB handles shared across threads. You can turn the checking off, but I had
	# db issues when it was disabled. This is a much more robust fix~~
	#
	# Migrated to PostgreSQL. We'll see how that works out.
	#
	# The log indirection is just so log statements include their originating thread. I like lots of logging.
	#
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def __getattribute__(self, name):

		threadName = threading.current_thread().name
		if name == "log" and "Thread-" in threadName:
			if threadName not in self.loggers:
				self.loggers[threadName] = logging.getLogger("%s.Thread-%d" % (self.loggerPath, self.lastLoggerIndex))
				self.lastLoggerIndex += 1
			return self.loggers[threadName]


		elif name == "conn":
			if threadName not in self.dbConnections:

				# First try local socket connection, fall back to a IP-based connection.
				# That way, if the server is local, we get the better performance of a local socket.
				try:
					self.dbConnections[threadName] = psycopg2.connect(dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)
				except psycopg2.OperationalError:
					self.dbConnections[threadName] = psycopg2.connect(host=settings.DATABASE_IP, dbname=settings.DATABASE_DB_NAME, user=settings.DATABASE_USER,password=settings.DATABASE_PASS)

				# self.dbConnections[threadName].autocommit = True
			return self.dbConnections[threadName]


		else:
			return object.__getattribute__(self, name)


	validKwargs = ["dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]

	def __init__(self):

		self.table = sql.Table(self.tableName.lower())

		self.cols = (
				self.table.dbid,
				self.table.dlstate,
				self.table.sourcesite,
				self.table.sourceurl,
				self.table.retreivaltime,
				self.table.lastupdate,
				self.table.sourceid,
				self.table.seriesname,
				self.table.filename,
				self.table.originname,
				self.table.downloadpath,
				self.table.flags,
				self.table.tags,
				self.table.note
			)


		self.colMap = {
				"dbid"          : self.table.dbid,
				"dlstate"       : self.table.dlstate,
				"sourcesite"    : self.table.sourcesite,
				"sourceurl"     : self.table.sourceurl,
				"retreivaltime" : self.table.retreivaltime,
				"lastupdate"    : self.table.lastupdate,
				"sourceid"      : self.table.sourceid,
				"seriesname"    : self.table.seriesname,
				"filename"      : self.table.filename,
				"originname"    : self.table.originname,
				"downloadpath"  : self.table.downloadpath,
				"flags"         : self.table.flags,
				"tags"          : self.table.tags,
				"note"          : self.table.note
			}


		self.loggers = {}
		self.dbConnections = {}
		self.lastLoggerIndex = 1

		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Runner BaseClass", self.pluginName)
		self.openDB()
		self.checkInitPrimaryDb()

	# Deferred to special hook in __getattribute__ that provides separate
	# db interfaces to each thread.
	def openDB(self):
		pass


	def closeDB(self):
		self.log.info("Closing DB...",)
		self.conn.close()
		self.log.info("DB Closed")


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Filesystem stuff
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):

		if self.shouldCanonize:
			canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		else:
			canonSeriesName = seriesName

		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		if canonSeriesName in nt.dirNameProxy:
			self.log.info("Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.baseDir, safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					return targetDir, True

				except FileExistsError:
					# Probably means the directory was concurrently created by another thread in the background?
					self.log.critical("Directory doesn't exist, and yet it does?")
					self.log.critical(traceback.format_exc())
					pass
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())

			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				self.log.warning("Base series name: %s", seriesName)
				self.log.warning("Canonized series name: %s", canonSeriesName)
				self.log.warning("Safe canonized name: %s", safeBaseName)
			return targetDir, False


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Misc Utilities
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def keyToCol(self, key):
		key = key.lower()
		if not key in self.colMap:
			raise ValueError("Invalid column name '%s'" % key)
		return self.colMap[key]

	def sqlBuildConditional(self, **kwargs):
		operators = []

		# Short circuit and return none (so the resulting where clause is all items) if no kwargs are passed.
		if not kwargs:
			return None

		for key, val in kwargs.items():
			operators.append((self.keyToCol(key) == val))

		# This is ugly as hell, but it functionally returns x & y & z ... for an array of [x, y, z]
		# And allows variable length arrays.
		conditional = functools.reduce(opclass.and_, operators)
		return conditional


	def sqlBuildInsertArgs(self, **kwargs):

		cols = [self.table.sourcesite]
		vals = [self.tableKey]

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.insert(columns=cols, values=[vals])

		query, params = tuple(query)

		return query, params


	# Insert new item into DB.
	# MASSIVELY faster if you set commit=False (it doesn't flush the write to disk), but that can open a transaction which locks the DB.
	# Only pass commit=False if the calling code can gaurantee it'll call commit() itself within a reasonable timeframe.
	def insertIntoDb(self, commit=True, **kwargs):
		query, queryArguments = self.sqlBuildInsertArgs(**kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)





	def generateUpdateQuery(self, **kwargs):
		if "dbId" in kwargs:
			where = (self.table.dbid == kwargs.pop('dbId'))
		elif "sourceUrl" in kwargs:
			where = (self.table.sourceurl == kwargs.pop('sourceUrl'))
		else:
			raise ValueError("GenerateUpdateQuery must be passed a single unique column identifier (either dbId or sourceUrl)")

		cols = []
		vals = []

		for key, val in kwargs.items():
			key = key.lower()

			if key not in self.colMap:
				raise ValueError("Invalid column name for insert! '%s'" % key)
			cols.append(self.colMap[key])
			vals.append(val)

		query = self.table.update(columns=cols, values=vals, where=where)
		query, params = tuple(query)
		return query, params




	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntry(self, sourceUrl, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"] and self.shouldCanonize:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		# Clamp the retreivaltime to now, so parsing issues that result in invalid, future
		# time-stamps don't cause posts to stick to the top of the post list.
		if 'retreivalTime' in kwargs:
			if kwargs['retreivalTime'] > time.time():
				kwargs['retreivalTime'] = time.time()

		query, queryArguments = self.generateUpdateQuery(sourceUrl=sourceUrl, **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)


		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))

	# Update entry with key sourceUrl with values **kwargs
	# kwarg names are checked for validity, and to prevent possiblity of sql injection.
	def updateDbEntryById(self, rowId, commit=True, **kwargs):

		# Patch series name.
		if "seriesName" in kwargs and kwargs["seriesName"] and self.shouldCanonize:
			kwargs["seriesName"] = nt.getCanonicalMangaUpdatesName(kwargs["seriesName"])

		query, queryArguments = self.generateUpdateQuery(dbId=rowId, **kwargs)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", queryArguments)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, queryArguments)

		# print("Updating", self.getRowByValue(sourceUrl=sourceUrl))



	def deleteRowsByValue(self, commit=True, **kwargs):
		if len(kwargs) != 1:
			raise ValueError("getRowsByValue only supports calling with a single kwarg", kwargs)

		validCols = ["dbId", "sourceUrl", "dlState"]

		key, val = kwargs.popitem()
		if key not in validCols:
			raise ValueError("Invalid column query: %s" % key)

		where = (self.colMap[key.lower()] == val)

		query = self.table.delete(where=where)

		query, args = tuple(query)


		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("Args = ", args)

		with self.conn.cursor() as cur:
			with transaction(cur, commit=commit):
				cur.execute(query, args)



	def test(self):
		print("Testing")

		# print(self.sqlBuildInsertArgs(sourcesite='Wat', retreivaltime="lol"))
		# print(self.sqlBuildInsertArgs(sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))

		# print(self.updateDbEntry(sourceUrl='lol', sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))
		# print(self.updateDbEntryById(rowId='lol', sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))
		# print(self.updateDbEntryKey(sourcesite='Wat', retreivaltime="lol", lastupdate='herp', filename='herp', downloadpath='herp', tags='herp'))

		# self.deleteRowsByValue(dbId="lol")
		# self.deleteRowsByValue(sourceUrl="lol")
		# self.deleteRowsByValue(dlState="lol")

		self.getRowsByValue(dbId=5)
		self.getRowsByValue(sourceUrl="5")
		self.getRowsByValue(sourceUrl="5", limitByKey=False)


	def getRowsByValue(self, limitByKey=True, **kwargs):
		if limitByKey and self.tableKey:
			kwargs["sourceSite"] = self.tableKey


		where = self.sqlBuildConditional(**kwargs)

		wantCols = (
				self.table.dbid,
				self.table.dlstate,
				self.table.sourceurl,
				self.table.retreivaltime,
				self.table.lastupdate,
				self.table.sourceid,
				self.table.seriesname,
				self.table.filename,
				self.table.originname,
				self.table.downloadpath,
				self.table.flags,
				self.table.tags,
				self.table.note
				)

		query = self.table.select(*wantCols, order_by=sql.Desc(self.table.retreivaltime), where=where)

		query, quargs = tuple(query)

		if self.QUERY_DEBUG:
			print("Query = ", query)
			print("args = ", quargs)

		with self.conn.cursor() as cur:

			#wrap queryies in transactions so we don't have hanging db handles.
			with transaction(cur):
				cur.execute(query, quargs)
				rets = cur.fetchall()


		retL = []
		for row in rets:

			keys = ["dbId", "dlState", "sourceUrl", "retreivalTime", "lastUpdate", "sourceId", "seriesName", "fileName", "originName", "downloadPath", "flags", "tags", "note"]
			retL.append(dict(zip(keys, row)))
		return retL

	# Insert new tags specified as a string kwarg (tags="tag Str") into the tags listing for the specified item
	def addTags(self, **kwargs):
		validCols = ["dbId", "sourceUrl", "dlState"]
		if not any([name in kwargs for name in validCols]):
			raise ValueError("addTags requires at least one fully-qualified argument (%s). Passed args = '%s'" % (validCols, kwargs))

		if not "tags" in kwargs:
			raise ValueError("You have to specify tags you want to add as a kwarg! '%s'" % (kwargs))

		tags = kwargs.pop("tags")
		# print("Getting row", kwargs)
		row = self.getRowByValue(**kwargs)
		if not row:
			raise ValueError("Row specified does not exist!")

		if row["tags"]:
			existingTags = set(row["tags"].split(" "))
		else:
			existingTags = set()

		newTags = set()
		for tagTemp in set(tags.split(" ")):

			# colon literals (":") break the `tsvector` index. Remove them (they're kinda pointless anyways)
			tagTemp = tagTemp.replace("&", "_")   \
							.replace(":", "_")    \
							.strip(".")           \
							.lower()
			newTags.add(tagTemp)


		tags = existingTags | newTags

		# make the tag ordering determistic by converting to a list, and sorting.
		tags = list(tags)
		tags.sort()

		tagStr = " ".join(tags)
		while "  " in tagStr:
			tagStr = tagStr.replace("  ", " ")
		tagStr = tagStr.lower()
		self.updateDbEntry(row["sourceUrl"], tags=tagStr)




	# Insert new tags specified as a string kwarg (tags="tag Str") into the tags listing for the specified item
	def removeTags(self, **kwargs):
		validCols = ["dbId", "sourceUrl", "dlState"]
		if not any([name in kwargs for name in validCols]):
			raise ValueError("addTags requires at least one fully-qualified argument (%s). Passed args = '%s'" % (validCols, kwargs))

		if not "tags" in kwargs:
			raise ValueError("You have to specify tags you want to add as a kwarg! '%s'" % (kwargs))

		tags = kwargs.pop("tags")
		row = self.getRowByValue(**kwargs)
		if not row:
			raise ValueError("Row specified does not exist!")

		if not row["tags"]:
			existingTags = set(row["tags"].split(" "))
		else:
			existingTags = set()

		newTags = set(tags.split(" "))

		tags = existingTags - newTags

		tagStr = " ".join(tags)
		while "  " in tagStr:
			tagStr = tagStr.replace("  ", " ")

		self.updateDbEntry(row["sourceUrl"], tags=tagStr)




	# Convenience crap.
	def getRowByValue(self, **kwargs):
		rows = self.getRowsByValue(**kwargs)
		if not rows:
			return []
		else:
			return rows.pop(0)


	def resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")
		with self.conn.cursor() as cur:
			cur.execute('''UPDATE {tableName} SET dlState=0 WHERE dlState=1 AND sourceSite=%s'''.format(tableName=self.tableName), (self.tableKey, ))
		self.conn.commit()
		self.log.info("Download reset complete")



	def processLinksIntoDB(self, linksDicts):

		self.log.info( "Inserting...",)
		newItems = 0
		for link in linksDicts:
			if link is None:
				print("linksDicts", linksDicts)
				print("WAT")

			row = self.getRowsByValue(sourceUrl=link["sourceUrl"], limitByKey=False)

			if not row:
				newItems += 1

				if not "dlState" in link:
					link['dlState'] = 0

				# Patch series name.
				if 'seriesName' in link and self.shouldCanonize:
					link["seriesName"] = nt.getCanonicalMangaUpdatesName(link["seriesName"])


				# Using fancy dict hijinks now. Old call below for reference.

				# self.insertIntoDb(retreivalTime = link["date"],
				# 					sourceUrl   = link["dlLink"],
				# 					originName  = link["dlName"],
				# 					dlState     = 0,
				# 					seriesName  = link["baseName"],
				# 					flags       = flagStr)

				self.insertIntoDb(**link)


				self.log.info("New item: %s", link)




		self.log.info( "Done")
		self.log.info( "Committing...",)
		self.conn.commit()
		self.log.info( "Committed")

		return newItems



	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Management
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	def checkInitPrimaryDb(self):
		with self.conn.cursor() as cur:

			cur.execute('''CREATE TABLE IF NOT EXISTS {tableName} (
												dbId          SERIAL PRIMARY KEY,
												sourceSite    TEXT NOT NULL,
												dlState       INTEGER NOT NULL,
												sourceUrl     text UNIQUE NOT NULL,
												retreivalTime double precision NOT NULL,
												lastUpdate    double precision DEFAULT 0,
												sourceId      text,
												seriesName    CITEXT,
												fileName      text,
												originName    text,
												downloadPath  text,
												flags         CITEXT,
												tags          CITEXT,
												note          text);'''.format(tableName=self.tableName))


			cur.execute("SELECT relname FROM pg_class;")
			haveIndexes = cur.fetchall()
			haveIndexes = [index[0] for index in haveIndexes]



			indexes = [
				("%s_source_index"           % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite                                            );'''  ),
				("%s_time_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivalTime                                         );'''  ),
				("%s_lastUpdate_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (lastUpdate                                            );'''  ),
				("%s_url_index"              % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceUrl                                             );'''  ),
				("%s_seriesName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName                                            );'''  ),
				("%s_tags_index"             % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (tags                                                  );'''  ),
				("%s_flags_index"            % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (flags                                                 );'''  ),
				("%s_dlState_index"          % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (dlState                                               );'''  ),
				("%s_originName_index"       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (originName                                            );'''  ),
				("%s_aggregate_index"        % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (seriesName, retreivalTime, dbId                       );'''  ),
				('%s_special_full_idx'       % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (retreivaltime DESC, seriesName DESC, dbid             );'''  ),
				('%s_special_granulated_idx' % self.tableName, self.tableName, '''CREATE INDEX %s ON %s (sourceSite, retreivaltime DESC, seriesName DESC, dbid );'''  ),

				# Create a ::tsvector GiN index on the tags column, so we can search by tags quickly.
				("%s_tags_gin_index"         % self.tableName, self.tableName, '''CREATE INDEX %s ON %s USING gin((lower(tags)::tsvector)                      );'''  ),
				# "%s_tags_gin_index"         % self.tableName, self.tableName, '''CREATE INDEX mangaitems_tags_gin_index ON mangaitems gin((lower(tags)::tsvector));'''
			]

			# CREATE INDEX hentaiitems_tags_gin_index ON hentaiitems USING gin((lower(tags)::tsvector));
			# CREATE INDEX mangaitems_tags_gin_index ON mangaitems USING gin((lower(tags)::tsvector));
			# CREATE INDEX hentaiitems_oname_trigram ON hentaiitems USING gin (originname gin_trgm_ops);
			# CREATE INDEX mangaitems_oname_trigram ON mangaitems USING gin (originname gin_trgm_ops);
			# UPDATE hentaiitems SET tags = replace(tags, ':', '_')
			# UPDATE hentaiitems SET tags = lower(tags)

			for name, table, nameFormat in indexes:
				if not name.lower() in haveIndexes:
					cur.execute(nameFormat % (name, table))



		self.conn.commit()
		self.log.info("Retreived page database created")


if __name__ == "__main__":
	import settings
	class TestClass(ScraperDbBase):



		pluginName = "Wat?"
		loggerPath = "Wat?"
		dbName = settings.DATABASE_DB_NAME
		tableKey = "test"
		tableName = "MangaItems"

		def go(self):
			print("Go?")



	import utilities.testBase as tb

	with tb.testSetup():
		obj = TestClass()
		obj.QUERY_DEBUG = True
		print(obj)
		obj.test()


