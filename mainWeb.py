#!flask/bin/python
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")

import scanner.logSetup
if __name__ == "__main__":
	scanner.logSetup.initLogging()

import threading
import time
import calendar


import datetime
import sys
import cherrypy
import logging

from inspector import app

def run_server():

	listen_address = "0.0.0.0"
	listen_port    = 8082

	if not "debug" in sys.argv:
		print("Starting background thread")
		# bk_thread = startBackgroundThread()

	if "debug" in sys.argv:
		print("Running in debug mode.")
		app.run(host=listen_address, port=listen_port, debug=True)
	else:
		print("Running in normal mode.")
		# app.run(host=listen_address, port=listen_port, processes=10)
		# app.run(host=listen_address, port=listen_port, threaded=True)



		def fixup_cherrypy_logs():
			loggers = logging.Logger.manager.loggerDict.keys()
			for name in loggers:
				if name.startswith('cherrypy.'):
					print("Fixing %s." % name)
					logging.getLogger(name).propagate = 0


		cherrypy.tree.graft(app, "/")
		cherrypy.server.unsubscribe()

		# Instantiate a new server object
		server = cherrypy._cpserver.Server()
		# Configure the server object
		server.socket_host = listen_address

		server.socket_port = listen_port
		server.thread_pool = 8

		# For SSL Support
		# server.ssl_module            = 'pyopenssl'
		# server.ssl_certificate       = 'ssl/certificate.crt'
		# server.ssl_private_key       = 'ssl/private.key'
		# server.ssl_certificate_chain = 'ssl/bundle.crt'

		# Subscribe this server
		server.subscribe()

		# fixup_cherrypy_logs()

		if hasattr(cherrypy.engine, 'signal_handler'):
			cherrypy.engine.signal_handler.subscribe()
		# Start the server engine (Option 1 *and* 2)
		cherrypy.engine.start()
		cherrypy.engine.block()
		# fixup_cherrypy_logs()



	print()
	print("Interrupt!")
	# if not "debug" in sys.argv:
	# 	print("Joining on background thread")
	# 	flags.RUNSTATE = False
	# 	bk_thread.join()

	# print("Thread halted. App exiting.")
	#
def run_web():


	# It looks like cherrypy installs a ctrl+c handler, so I don't need to.
	run_server()



if __name__ == "__main__":
	started = False
	if not started:
		started = True
		run_web()
