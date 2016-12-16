#!/usr/bin/env bash

source venv/bin/activate

until python3 runDedupServer.py; do
    echo "Server 'python3 runDedupServer.py' crashed with exit code $?.  Respawning.." >&2
    sleep 1
done