#!/bin/bash


# python3 -m unittest Tests.DbContentTests

# coverage run --source=./dbApi.py -m unittest Tests.DbApiTests

# Coverage doesn't work with cython files.
# Therefore, we don't run the BK Tree tests with it.
# python3 -m unittest Tests.BinaryConverterTests
# python3 -m unittest Tests.BKTreeTests
# python3 -m unittest Tests.Test_BKTree_Concurrency


# Test ALL THE THINGS

set -e

valgrind                                             \
	--leak-check=yes                                 \
	--suppressions=/usr/lib/valgrind/python3.supp    \
python3 $(which nosetests)                           \
	--exe                                            \
	--stop                                           \
	--nocapture                                      \
	Tests.Test_DuplicateArchiveDetector 2>&1 | tee grind.txt
	# Tests.Test_BKTree_Concurrency_Mem 2>&1 | tee grind.txt
