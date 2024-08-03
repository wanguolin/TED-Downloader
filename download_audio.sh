#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_lst_file> <output_directory>"
    exit 1
fi

lst_file="$1"
output_dir="$2"

if [ ! -f "$lst_file" ]; then
    echo "File not found: $lst_file"
    exit 1
fi

if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi

if ! command -v ffmpeg &> /dev/null
then
    echo "ffmpeg could not be found, please install it first."
    exit 1
fi

while IFS= read -r url
do
    if [ -z "$url" ]; then
        continue
    fi

    id=$(basename "$url" | sed 's/\?.*//;s/\.[^.]*$//')

    output_file="${output_dir}/${id}.m4a"

    if [ -f "$output_file" ]; then
        echo "File $output_file already exists, skipping."
    else
        echo "Processing $url..."
        ffmpeg -hide_banner -nostdin -i "$url" -c:a aac -b:a 64k -map a "$output_file" -loglevel warning 2>> "${output_dir}/ffmpeg_errors.log"
    fi
done < "$lst_file"