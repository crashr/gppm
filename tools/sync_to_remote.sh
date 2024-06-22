#!/bin/bash

SRC="./"
DEST="pc06:~/gppm"
#LOGFILE="/var/log/rsync.log"

inotifywait -m -r -e modify,create,delete,move "$SRC" --format '%w%f' |
while read file; do
    rsync -avz "$SRC" "$DEST" #>> "$LOGFILE" 2>&1
done