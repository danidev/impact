#!/bin/bash

# Define source and destination
SOURCE_DIR="/home/daniele/git/caffeinated/smallprojects/synth-video"
REMOTE_HOST="daniele@192.168.1.111"
REMOTE_DIR="~"

# Display what we're about to do
echo "Syncing $SOURCE_DIR to $REMOTE_HOST:$REMOTE_DIR"

# Run rsync with common options:
# -a: archive mode (preserves permissions, timestamps, etc.)
# -v: verbose output
# -z: compress data during transfer
# --progress: show progress during transfer
# --delete: delete files on the receiving side that don't exist on the sending side
rsync -avz --progress --delete "$SOURCE_DIR" "$REMOTE_HOST:$REMOTE_DIR"

echo "Sync completed!"
