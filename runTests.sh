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

for i in `seq 1 10`;
do

	python3 $(which nosetests)                       \
		--with-coverage                              \
		--exe                                        \
		--cover-package=dbApi                        \
		--cover-package=scanner.hashFile             \
		--cover-package=dbPhashApi                   \
		--cover-package=deduplicator.rwlock          \
		--cover-package=deduplicator.ProcessArchive  \
		--stop
		# --nocapture
done;

# python3 $(which nosetests) --with-coverage --exe --cover-package=deduplicator.ProcessArchive Tests.Test_DuplicateArchiveDetector

coverage report --show-missing

coverage erase

