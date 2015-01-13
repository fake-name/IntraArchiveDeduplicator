
import argparse
import scanner.scanner
import deduplicator.ProcessArchive

import sys





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

	print("Sys args: ", sys.argv)


	# ---------------  Processing  ----------------------
	archProc = subparsers.add_parser('arch-process', help="Scan set of directory, and generate a list of hashes of all the files therein")
	archProc.add_argument('-i', '--in-archive',   required=True,  dest="sourcePath")
	archProc.add_argument('-n', '--nophash',     required=False, dest="noPhash", action='store_true')
	archProc.add_argument('-c', '--nocontext',     required=False, dest="noContext", action='store_true')

	archProc.set_defaults(func=deduplicator.ProcessArchive.commandLineProcess)


	# ---------------  Tree Management  ----------------------
	archProc = subparsers.add_parser('tree-reload', help="Reload the phash-tree from the database")

	archProc.set_defaults(func=deduplicator.ProcessArchive.commandLineReloadTree)




	argsParsed = parser.parse_args()
	if len(sys.argv) > 1:
		argsParsed.func(argsParsed)
	else:
		print("You must specify the operating mode. 'dir-scan' is the only supported mode currently")
