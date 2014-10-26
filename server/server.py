

import rpyc
from rpyc.utils.server import ThreadedServer
import dbApi
import deduplicator.dupCheck
import logSetup

class DbInterfaceServer(rpyc.Service):

	# def __init__(self, *args, **kwargs):
	# 	print("Init called!")
	# 	super(self).__init__(self, *args, **kwargs)

	def on_connect(self):
		print("Connection established!")



	def on_disconnect(self):
		print("Disconnected!")



	class exposed_TreeProcessor(deduplicator.dupCheck.TreeProcessor):

		def exposed_trimFiles(self, *args, **kwargs):
			super().trimFiles(*args, **kwargs)
		pass

def run_server():
	print("Starting.")
	server = ThreadedServer(DbInterfaceServer, port = 12345)
	server.start()

import server_reloader

def main():
	logSetup.initLogging()
	server_reloader.main(
		run_server,
		before_reload=lambda: print('Reloading code...')
	)

if __name__ == '__main__':
	main()
