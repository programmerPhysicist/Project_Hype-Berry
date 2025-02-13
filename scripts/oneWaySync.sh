#!/bin/bash
# This script should work, as long you keep in
# the same location in relation to the python code.
scriptdir=$(dirname "${BASH_SOURCE[0]}")
LOG_PATH=$XDG_STATE_HOME/oneWaySync/oneWaySync.log
exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>>"$LOG_PATH" 2>&1

echo "Running at..."
date
cd "$scriptdir/../source"
python3 one_way_sync.py
