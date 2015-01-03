

import rpyc
from rpyc.utils.server import ThreadedServer
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

	def exposed_processDownload(self, *args, locked=True, **kwargs):
		if locked:
			print("Acquiring lock")
			self.lock.acquire()
		try:
			return deduplicator.ProcessArchive.processDownload(*args, **kwargs)
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
	server = ThreadedServer(service=DbInterfaceServer, port = 12345, hostname='localhost', logger=serverLog)
	server.start()



def before_exit():
	print("Caught exit! Exiting")


import server_reloader

def main():
	scanner.logSetup.initLogging()

	print("Preloading cache directories")

	tree = dbPhashApi.PhashDbApi()
	# print("Testing reload")
	# server.tree.tree.reloadTree()
	# print("Starting RPC server")

	run_server()

	# server_reloader.main(
	# 	run_server
	# )

if __name__ == '__main__':
	main()
