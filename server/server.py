

import rpyc
from rpyc.utils.server import ThreadedServer
import dbApi
import deduplicator.dupCheck
import logSetup

import server.tree

class DbInterfaceServer(rpyc.Service):

	# def __init__(self, *args, **kwargs):
	# 	print("Init called!")
	# 	super(self).__init__(self, *args, **kwargs)

	def on_connect(self):
		print("Connection established!")

	def on_disconnect(self):
		print("Disconnected!")

	def exposed_loadTree(self, *args, **kwargs):
		print(server.tree.tree)
		server.tree.tree.loadTree(*args, **kwargs)

	class exposed_ArchChecker(deduplicator.dupCheck.ArchChecker):
		def exposed_isBinaryUnique(self, *args, **kwargs):
			return super().isBinaryUnique(*args, **kwargs)
		def exposed_isPhashUnique(self, *args, **kwargs):
			return super().isPhashUnique(*args, **kwargs)
		def exposed_getHashes(self, *args, **kwargs):
			return super().getHashes(*args, **kwargs)
		def exposed_deleteArch(self, *args, **kwargs):
			return super().deleteArch(*args, **kwargs)
		def exposed_addNewArch(self, *args, **kwargs):
			return super().addNewArch(*args, **kwargs)


	class exposed_TreeProcessor(deduplicator.dupCheck.TreeProcessor):
		def exposed_trimTree(self, *args, **kwargs):
			return super().trimTree(*args, **kwargs)

		def exposed_trimFiles(self, *args, **kwargs):
			return super().trimFiles(*args, **kwargs)

		def exposed_removeArchive(self, *args, **kwargs):
			return super().removeArchive(*args, **kwargs)


def run_server():
	print("Started.")
	server = ThreadedServer(DbInterfaceServer, port = 12345)
	server.start()


def before_reload():
	if not server.tree.tree:
		print("Need to create tree")
		server.tree.tree = deduplicator.dupCheck.TreeRoot()
	print("Loading")

def before_exit():
	print("Caught exit! Exiting")


import server_reloader

def main():
	logSetup.initLogging()
	before_reload()
	run_server()
	# server_reloader.main(
	# 	run_server,
	# 	before_reload=before_reload,
	# 	before_exit=before_exit
	# )

if __name__ == '__main__':
	main()
