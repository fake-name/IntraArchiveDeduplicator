

import rpyc
import dbPhashApi
from rpyc.utils.server import ThreadedServer
import logging
import scanner.logSetup
import server.decorators

import scanner.hashFile

#TODO: A much cleaner message-passing interface here would be quite nice

class DbInterfaceServer(rpyc.Service):



	def on_connect(self):
		print("Client Connection established!")

	def on_disconnect(self):
		print("Client Disconnected!")

	# def exposed_loadTree(self, *args, **kwargs):
	# 	print(server.tree.tree)
	# 	server.tree.tree.loadTree(*args, **kwargs)

	# def exposed_reloadTree(self, *args, **kwargs):
	# 	print(server.tree.tree)
	# 	server.tree.tree.reloadTree(*args, **kwargs)

	# def exposed_nodeCount(self):
	# 	return server.tree.tree.nodes


	# @server.decorators.exposify
	# class exposed_ArchChecker(deduplicator.dupCheck.ArchChecker):
	# 	pass

	# @server.decorators.exposify
	# class exposed_TreeProcessor(deduplicator.dupCheck.TreeProcessor):
	# 	pass

	def exposed_getMd5Hash(self, fCont):
		return scanner.hashFile.getMd5Hash(fCont)

	def exposed_hashFile(self, fsPath, intPath, fCont, shouldPhash=True):
		return scanner.hashFile.hashFile(fsPath, intPath, fCont, shouldPhash)


	@server.decorators.exposify
	class exposed_DbApi(dbPhashApi.PhashDbApi):
		pass




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
