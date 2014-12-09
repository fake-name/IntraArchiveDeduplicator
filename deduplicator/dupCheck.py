


import UniversalArchiveInterface
import os
import os.path
import logging
import server.tree
import dbPhashApi
import shutil
import traceback
import threading
import sql.operators as sqlo

import scanner.hashFile as hashFile

import pyximport
print("Have Cython")
pyximport.install()

import deduplicator.cyHamDb as hamDb

PHASH_DISTANCE_THRESHOLD = 2

