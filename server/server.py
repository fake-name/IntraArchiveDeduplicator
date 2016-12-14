

import rpyc
from rpyc.utils.server import ThreadPoolServer
import dbPhashApi
import deduplicator.ProcessArchive
import scanner.hashFile
import logging
import scanner.logSetup
import scanner.fileHasher


import server.decorators
import multiprocessing
import dbApi
import sys



class DbInterfaceServer(rpyc.Service):
	lock = multiprocessing.RLock()

	def exposed_processDownload(self, *args, locked=False, **kwargs):
		if locked:
			print("Acquiring lock")
			self.lock.acquire()
		try:
			return deduplicator.ProcessArchive.processDownload(*args, **kwargs)
		finally:
			if locked:
				print("Releasing lock")
				self.lock.release()

	def exposed_listDupes(self, *args, locked=False, **kwargs):
		print("ListDupes call: ", (args, kwargs))
		if locked:
			print("Acquiring lock")
			self.lock.acquire()
		try:
			return deduplicator.ProcessArchive.getSignificantlySimilarArches(*args, **kwargs)
		finally:
			if locked:
				print("Releasing lock")
				self.lock.release()

	def exposed_reloadTree(self):
		treeProx = dbPhashApi.PhashDbApi()
		treeProx.forceReload()




def run_server():
	print("Started.")
	serverLog = logging.getLogger("Main.RPyCServer")
	srv = ThreadPoolServer(service=DbInterfaceServer, port = 12345, hostname='localhost', logger=serverLog, nbThreads=6)
	srv.start()



def before_exit():
	print("Caught exit! Exiting")


import datetime
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool        import ThreadPoolExecutor



# Convenience functions to make intervals clearer.
def days(num):
	return 60*60*24*num
def hours(num):
	return 60*60*num
def minutes(num):
	return 60*num


def reload_tree():
	treeProx = dbPhashApi.PhashDbApi()
	treeProx.forceReload()


def configure_scheduler():

	sched = BackgroundScheduler({
			'apscheduler.jobstores.default': {
				'type': 'memory'
			},
			'apscheduler.executors.default': {
				'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
				'max_workers': '10'
			},
			'apscheduler.job_defaults.coalesce': 'true',
			'apscheduler.job_defaults.max_instances': '2',
		})

	startTime = datetime.datetime.now(tz=pytz.utc)+datetime.timedelta(seconds=5)

	sched.add_job(reload_tree,
				trigger            = 'interval',
				seconds            = hours(6),
				next_run_time      = startTime,
				id                 = "tree-reloader",
				replace_existing   = True,
				max_instances      = 1,
				coalesce           = True,
				misfire_grace_time = 2**30)

	return sched

def main():
	scanner.logSetup.initLogging()

	print("Preloading cache directories")

	scheduler = configure_scheduler()
	tree = dbPhashApi.PhashDbApi()

	scheduler.start()
	print("Tree load via scheduler in 5 seconds...")

	run_server()


	scheduler.shutdown()

	# server_reloader.main(
	# 	run_server
	# )

if __name__ == '__main__':
	main()
