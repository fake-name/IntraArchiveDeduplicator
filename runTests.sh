#!/bin/bash


# python3 -m unittest Tests.DbContentTests

# coverage run --source=./dbApi.py -m unittest Tests.DbApiTests

# Coverage doesn't work with cython files.
# Therefore, we don't run the BK Tree tests with it.
# python3 -m unittest Tests.BinaryConverterTests
# python3 -m unittest Tests.BKTreeTests

# coverage report
# coverage report --show-missing
# coverage erase


# python3 $(which nosetests) --with-coverage --exe --cover-package=dbApi --cover-package=scanner.hashFile
# python3 $(which nosetests) --exe Tests.Test_PhashDbApi_Basic
python3 $(which nosetests) --exe Tests.Test_PhashDbApi_PHashStuff -s

