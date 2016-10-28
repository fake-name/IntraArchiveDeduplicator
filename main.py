
import traceback
import sys
import argparse
import scanner.scanner
import interactive_tests.test_interface
import deduplicator.ProcessArchive






if __name__ == "__main__":
	# signal.signal(signal.SIGINT, signal.SIG_IGN)


	# procDdTool = proc.DedupTool()

	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands')

	# ---------------  Scanning  ----------------------
	parserDirScan = subparsers.add_parser('dir-scan', help="Scan set of directory, and generate a list of hashes of all the files therein")
	parserDirScan.add_argument('-i', '--in-folder',   required=True,  dest="sourcePath")
	parserDirScan.add_argument('-n', '--no-clean',    required=False, dest="noCleanTemps", action='store_true')
	parserDirScan.add_argument('-p', '--purge',       required=False, dest="purge", action='store_true')
	parserDirScan.add_argument('-t', '--threads',     required=False, dest="threadNo")
	parserDirScan.add_argument('-s', '--nophash',     required=False, dest="noPhash", action='store_true')
	parserDirScan.add_argument('-c', '--noIntegrity', required=False, dest="noIntegrityCheck", action='store_true')
	parserDirScan.set_defaults(func=scanner.scanner.doScan)
	parserDirScan.set_defaults(subproc=parserDirScan)



	# ---------------  Processing  ----------------------
	archProc = subparsers.add_parser('arch-process', help="Scan set of directory, and generate a list of hashes of all the files therein")
	archProc.add_argument('-i', '--in-archive',   required=True,  dest="sourcePath")
	archProc.add_argument('-n', '--nophash',     required=False, dest="noPhash", action='store_true')
	archProc.add_argument('-c', '--nocontext',     required=False, dest="noContext", action='store_true')

	archProc.set_defaults(func=deduplicator.ProcessArchive.commandLineProcess)
	archProc.set_defaults(subproc=archProc)


	# ---------------  Tree Management  ----------------------
	archProc = subparsers.add_parser('tree-reload', help="Reload the phash-tree from the database")
	archProc.set_defaults(func=deduplicator.ProcessArchive.commandLineReloadTree)
	archProc.set_defaults(subproc=archProc)


	# ---------------  Testing  ----------------------
	testProc = subparsers.add_parser('test', help="test-functions")
	testProc.add_argument('-f', '--test-file',    required=False,  dest="testScan",    help="Scan an archive, and print it's resulting hashes to the console.")
	testProc.add_argument('-s', '--list-similar', required=False,  dest="listSimilar", help="Scan an archive, and print archives with many phash-results in common.")
	testProc.set_defaults(func=interactive_tests.test_interface.go)
	testProc.set_defaults(subproc=testProc)





	argsParsed = parser.parse_args()
	if len(sys.argv) > 1:
		try:
			argsParsed.func(argsParsed)
		except Exception:
			print()
			parser.print_help()
			argsParsed.subproc.print_help()
			raise
	else:
		parser.print_help()
