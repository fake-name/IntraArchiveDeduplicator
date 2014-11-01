#!/bin/bash

coverage run --source=./dbApi.py -m unittest Tests.DbApiTests
coverage report
coverage report --show-missing
