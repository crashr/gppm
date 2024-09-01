#!/bin/bash

# Description:
# This script synchronizes a source directory to a remote destination using rsync.
# It uses inotifywait to monitor the source directory for changes and then synchronizes the changes to the destination.
# The source and destination directories are specified as command line arguments.

# Check if source and destination are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_directory> <destination_directory>"
    exit 1
fi

SRC="$1"
DEST="$2"
#LOGFILE="/var/log/rsync.log"

inotifywait -m -r -e modify,create,delete,move "$SRC" --format '%w%f' |
while read file; do
    #rsync -avz --include='build/*.deb' --exclude='build/*' "$SRC" "$DEST" #>> "$LOGFILE" 2>&1
    rsync -avz --include='build/*' "$SRC" "$DEST" #>> "$LOGFILE" 2>&1
done
