
import argparse
import scanner
import proc
import sys

import runState
import signal
if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal.SIG_IGN)


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

	parserDirScan.set_defaults(func=scanner.doScan)

	# # --------------- Processing ----------------------

	parserDirScan = subparsers.add_parser('dir-clean', help="Load set of cached hashes, and move all duplicate zips therein")
	parserDirScan.add_argument('-i', '--in-folder', required=True, dest="targetDir")

	# parserDirScan.add_argument('--move', required=False, dest="movePath")
	# parserDirScan.add_argument('--move-go', required=False, dest="doMove", action='store_true')

	# match-externals means chose and delete the files *outside* of the target path that are duplicates of the files *in* the target path
	parserDirScan.add_argument("-e", '--match-externals', required=False, dest="externals", action='store_true')

	# parserDirRestore = subparsers.add_parser('restore', help="Load set of cached hashes, and move all duplicate zips therein")
	# parserDirRestore.add_argument('-i', '--in-folder', required=False, dest="filterPath")

	parserDirScan.set_defaults(func=proc.Deduper.dedupe)
	# parserDirRestore.set_defaults(func=procDdTool.restoreFiles)


	argsParsed = parser.parse_args()
	if len(sys.argv) > 1:
		print("Argparsed = ", argsParsed)
		argsParsed.func(argsParsed)
	else:
		print("You must specify the operating mode. Either 'dir-scan' or 'dir-clean'")
