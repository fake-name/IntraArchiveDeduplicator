IntraArchiveDeduplicator
========================

Tool for managing data-deduplication within extant compressed archive files, with a heavy focus on Manga/Comic-book archive files.

This is a rather exotic tool that is intended to allow fairly fast duplicate detection for files *within* compressed archives. 

It maintains a database of hashes for all files it scans, and actually recurses into compressed archives to 
scan the files within the archives, which should allow detection of archives with duplicate contents, even
if the archives are compressed using different compression algorithms.

There are also preliminary components for further deduplication using perceptual-hashing of image files within the archives. 

Right now, the scanning and DB maintenance functionality is largely functional, but the logic to actually do deduplication is not
yet implemented. However, my [MangaCMS](https://github.com/fake-name/MangaCMS/) project [already has some support](https://github.com/fake-name/MangaCMS/tree/master/deduplicator) for detecting 
when a newly downloaded file has entirely duplicated content, and the automatic removal of the new file to prevent further
introduction of duplcates.
