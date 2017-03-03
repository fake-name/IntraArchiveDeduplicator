

# Your postgres SQL database credentials for the deduper.
# the PSQL_USER must have write access to the database PSQL_DB_NAME

PSQL_IP      = "server IP"
PSQL_PASS    = "password"

PSQL_USER    = "deduper"
PSQL_DB_NAME = "deduper_db"

# Directories to preload the hashes for in the BK tree.
PRELOAD_DIRECTORIES = []
mangaFolders     = {}

masked_path_prefixes = []
