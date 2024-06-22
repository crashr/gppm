#!/bin/bash

SRC_DIR="./"

COMMAND="python3 gppmd.py --config gppmd_config.yaml"

start_command() {
    echo "Starting command..."
    $COMMAND &
    COMMAND_PID=$!
    echo "Command started with PID $COMMAND_PID"
}

stop_command() {
    if [ -n "$COMMAND_PID" ]; then
        echo "Stopping command with PID $COMMAND_PID..."
        kill $COMMAND_PID
        wait $COMMAND_PID 2>/dev/null
        echo "Command stopped."
    fi
}

trap stop_command EXIT

start_command

inotifywait -m -r -e modify,create,delete,move "$SRC_DIR" |
while read -r directory events filename; do
    echo "Change detected in $directory$filename: $events"
    stop_command
    start_command
done
