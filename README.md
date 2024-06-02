# TED Downloader

## Introduction
This script fetches TED Talks metadata and details, and can also download subtitles for the talks. It serves as a utility for my side project, TED Classroom ***coming soon***. TED Classroom is a web app that will allow users to watch TED Talks with AI-enhanced features, such as advanced query, dictation, reading, and writing.

I have open-sourced this script to help others who wish to fetch TED content and download materials as needed.

## Dependencies
1. Tested with Python 3.10
2. Create a folder named `downloads` in the root directory of the project

## Usage
```bash
Using existing folder: downloads
usage: fetch.py [-h] [--fetch-meta] [--fetch-details] [--download-subtitles DOWNLOAD_SUBTITLES] [--lang LANG]

A script to fetch TED Talks meta data and details.

options:
  -h, --help            show this help message and exit
  --fetch-meta          Fetch meta data from TED Talks
  --fetch-details       Fetch details from TED Talks using local meta data
  --download-subtitles  ted_id
                        Fetch subtitles from TED Talks using the provided ID
  --lang LANG           Language code for subtitles, default is en
```

### --fetch-meta
This option fetches the meta data from TED Talks and stores it in a file named `meta.csv` in the `downloads` folder from "". The csv file has 3 columns regarding the downloads: `download_low, download_medium and download_1080p`, if you want to download the video in a specific quality, you can use your `Excel` to open the csv file and trim the respective column into a list file, then import them into a download tool to get them all.

### --fetch-details
Once you have `meta.csv` and want to fetch the details of the talks, such as summaries and subtitles, you can use this option. Fetching subtitles requires the `talk_id`, which necessitates a further details fetch after obtaining the metadata.

## To Do
1. Increasingly download which can leverage the existing files in `./downloads`
2. Statistics on the downloaded files, such as the failed downloads...
3. Add requirements.txt

## Contributions
I welcome contributions to this project. Please feel free to fork this repository and submit a pull request.
Email me at [wanguolin@gmail.com](mailto:wanguolin@gmail.com) if you have any questions.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
