

import traceback
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

from pympler import muppy
from pympler import summary
from pympler import tracker

import datetime
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool        import ThreadPoolExecutor



class DbInterfaceServer(rpyc.Service):

	def exposed_processDownload(self, *args, **kwargs):
		return deduplicator.ProcessArchive.processDownload(*args, **kwargs)

	def exposed_listDupes(self, *args, **kwargs):
		return deduplicator.ProcessArchive.getSignificantlySimilarArches(*args, **kwargs)

	def exposed_single_phash_search(self, phash, distance=4):
		db = dbPhashApi.PhashDbApi()

		matchids = db.getWithinDistance(phash, distance)
		return matchids

	def exposed_reloadTree(self):
		treeProx = dbPhashApi.PhashDbApi()
		treeProx.forceReload()



	def exposed_check(self):
		return "OK"




def run_server():
	print("Started.")
	serverLog = logging.getLogger("Main.RPyCServer")
	srv = ThreadPoolServer(service=DbInterfaceServer, port = 12345, hostname='0.0.0.0', logger=serverLog, nbThreads=6)
	srv.start()



def before_exit():
	print("Caught exit! Exiting")



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

TRACKER = None

def dump_objs():
	global TRACKER
	if TRACKER is None:
		TRACKER = tracker.SummaryTracker()

	with open("obj_log.txt", "a") as fp:
		fp.write("Memory at {}\n".format(str(datetime.datetime.now())))
		try:
			all_objects = muppy.get_objects()
			sum1 = summary.summarize(all_objects)
			str_sum  = summary.format_(sum1)

			fp.write("Summary:\n")
			for line in str_sum:
				fp.write("	{}\n".format(line))
		except Exception:
			err = traceback.format_exc()
			fp.write("Error: \n")
			fp.write(err)

		try:
			str_diff = TRACKER.format_diff()
			fp.write("Diff:\n")
			for line in str_diff:
				fp.write("	{}\n".format(line))
		except Exception:
			err = traceback.format_exc()
			fp.write("Error: \n")
			fp.write(err)

		fp.write("\n")

def configure_scheduler():

	dump_objs()
	dump_objs()

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

	sched.add_job(dump_objs,
				trigger            = 'interval',
				seconds            = minutes(30),
				next_run_time      = startTime,
				id                 = "leak-tracker",
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
