IntraArchiveDeduplicator
========================

Tool for managing data-deduplication within extant compressed archive files, with a heavy focus on Manga/Comic-book archive files.

This is a rather exotic tool that is intended to allow fairly fast duplicate detection for files *within* compressed archives.

It maintains a database of hashes for all files it scans, and actually recurses into compressed archives to
scan the files within the archives, which should allow detection of archives with duplicate contents, even
if the archives are compressed using different compression algorithms.

There are also facilities for searching by image similarity, using a custom tree system.

The image similarity system runs as a server on top of an existing PostgreSQL server, as it is implemented in
python (actually Cython, but basically python). It's fairly memory hungry. Currently, ~12M hashes takes about 5 GB
of RAM, or ~1Kbyte/hash. There is some room for optimization here.

Theoretically, each hash should take 64\*8 + 8 + (8 \* number of IDs at each node) (+ a few housekeeping) bytes. However,
right now, a number of the node attributes are stored as hashtables (the child-links, for example), so they
do not take as much space as they theoretically will if every child pointer pointed to a actual valid node.

Right now, the scanning and DB maintenance functionality is largely functional, but the logic to actually do
deduplication is very preliminary. My [MangaCMS](https://github.com/fake-name/MangaCMS/) project 
[already has some support](https://github.com/fake-name/MangaCMS/tree/master/deduplicator) for detecting when a 
newly downloaded file has entirely duplicated content, and the automatic removal of the new file to prevent further
introduction of duplicates.  


Dependencies:  

 - PostgreSQL >= 9.3 (Possibly any >9.0?)
 - Psycopg2
 - Cython
 - RPyC
 - Colorama
 - python-sql

For PHashing:  

 - Numpy
 - Scipy
 - Pillow

For Unit testing:

 - Coverage.py
 - Bitstring

There are fairly extensive unit tests for the DB API, as well as the BK-tree and the phashing systems. However, the great majority of the tests (all the DB API tests, which are 80%+ of them) require a local postgres instance, so they're not suitable for CI integration.


TODO:
Moved counter in CPPBKTree delete operation doesn't work.

Long filenames break hasher?
Bad filename: "00PGw6sr1r7fBlHub52mIRCQ4Nd5jTn0n31_2B3HvgCJTHDJcBK3qV0H7k7gdTwYTiaowENq0D8vK0hBDL_5d88vcInWqPRs4H8GZQYHRlzrHWUYNKiD0QRoeEOz2AztX4nF8v0=w1600"