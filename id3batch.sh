#!/bin/bash
# Batch fix CP1251 encoded ID3 tags in MP3 files
# Usage: id3batch.sh /path/to/directory

if [[ $# -eq 0 ]]; then
    echo "Usage: id3batch.sh <directory>"
    echo ""
    echo "Recursively finds all MP3 files in the directory and fixes"
    echo "CP1251 encoded ID3 tags to UTF-8 using id3fix.py"
    exit 1
fi

directory="$1"

if [[ ! -d "$directory" ]]; then
    echo "Error: Directory '$directory' does not exist"
    exit 1
fi

# Find all mp3 files recursively and process them
find "$directory" -type f -iname "*.mp3" | while read -r mp3_file; do
    id3fix.py -f "$mp3_file"
done
