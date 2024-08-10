#!/bin/bash

function show_help() {
    echo "Usage: $0 -d DIRECTORY"
    echo ""
    echo "Options:"
    echo "  -d DIRECTORY   Specify the directory to delete zero-size files from"
    echo "  -h             Show this help message"
    exit 1
}

while getopts "hd:" opt; do
    case ${opt} in
        d )
            directory=$OPTARG
            ;;
        h )
            show_help
            ;;
        * )
            show_help
            ;;
    esac
done

if [ -z "$directory" ]; then
    echo "Error: Directory not specified."
    show_help
fi

deleted_count=0

temp_file=$(mktemp)

find "$directory" -type f -size 0 > "$temp_file"

while read -r file; do
    rm -f "$file"
    echo "Deleted: $file"
    ((deleted_count++))
done < "$temp_file"

rm -f "$temp_file"

echo "Total files deleted: $deleted_count"