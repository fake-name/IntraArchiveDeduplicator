#!/bin/bash


# python3 -m unittest Tests.DbContentTests

# coverage run --source=./dbApi.py -m unittest Tests.DbApiTests

# Coverage doesn't work with cython files.
# Therefore, we don't run the BK Tree tests with it.
# python3 -m unittest Tests.BinaryConverterTests
# python3 -m unittest Tests.BKTreeTests


# Test ALL THE THINGS
python3 $(which nosetests)                       \
	--with-coverage                              \
	--exe                                        \
	--cover-package=dbApi                        \
	--cover-package=scanner.hashFile             \
	--cover-package=dbPhashApi                   \
	--cover-package=deduplicator.rwlock          \
	--cover-package=deduplicator.ProcessArchive

# python3 $(which nosetests) --with-coverage --exe --cover-package=deduplicator.ProcessArchive Tests.Test_DuplicateArchiveDetector

coverage report --show-missing

coverage erase

