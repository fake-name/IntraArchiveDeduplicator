

import rpyc
from rpyc.utils.server import ThreadedServer
import dbApi
import deduplicator.dupCheck

class DbInterfaceServer(rpyc.Service):

	# def __init__(self, *args, **kwargs):
	# 	print("Init called!")
	# 	super(self).__init__(self, *args, **kwargs)

	def on_connect(self):
		print("Connection established!")
		self.checker = False

	def exposed_open(self, archPath):
		self.checker = deduplicator.dupCheck.ArchChecker(archPath)

	def exposed_isBinaryUnique(self):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_simplePhashCheck(self):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_localBKPhash(self, dirPath):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_isPhashUnique(self):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_getHashes(self, shouldPhash=True):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_deleteArch(self):
		if not self.checker:
			raise ValueError("You need to open an archive first!")

	def exposed_addNewArch(self, shouldPhash=True):
		if not self.checker:
			raise ValueError("You need to open an archive first!")



	def on_disconnect(self):
		print("Disconnected!")


def run_server():
	print("Starting.")
	server = ThreadedServer(DbInterfaceServer, port = 12345)
	server.start()

import server_reloader

def main():
	server_reloader.main(
		run_server,
		before_reload=lambda: print('Reloading code…')
	)

if __name__ == '__main__':
	main()
