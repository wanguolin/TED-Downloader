# TED Downloader

## Introduction
This script fetches TED Talks metadata and details, and can also download subtitles for the talks. It serves as a utility for my side project, TED Classroom ***coming soon***. TED Classroom is a web app that will allow users to watch TED Talks with AI-enhanced features, such as advanced query, dictation, reading, and writing.

I have open-sourced this script to help others who wish to fetch TED content and download materials as needed.

## Dependencies
1. Tested with Python 3.10
2. Create a folder named `downloads` in the root directory of the project

## Usage

```bash
python fetch.py [-h] [--download-meta] [--download-details] [--download-subtitles DOWNLOAD_SUBTITLES] [--lang LANG] [--download-all] [--download-stats] [--download-audio {low,medium,high}]

A script to fetch TED Talks meta data and details.

options:
  -h, --help            show this help message and exit
  --download-meta       Fetch meta data from TED Talks
  --download-details    Fetch details from TED Talks using local meta data
  --download-subtitles DOWNLOAD_SUBTITLES
                        Fetch subtitles from TED Talks using the provided ID
  --lang LANG           Language code for subtitles, default is en
  --download-all        Download them all
  --download-stats      Calculate download success statistics
  --download-audio {low,medium,high}
                        Convert meta.csv into download_<quality>.lst. Default: low quality.
```

### --download-meta
This option fetches the meta data from TED Talks and stores it in a file named `meta.csv` in the `downloads` folder. The csv file contains information about each talk, including download links for different video qualities.

### --download-details
Once you have `meta.csv`, use this option to fetch additional details of the talks, including summaries and subtitles. This step is necessary to obtain the `ted_talk_id` required for subtitle downloads.

### --download-subtitles DOWNLOAD_SUBTITLES
Use this option to download subtitles for a specific TED Talk using its ID. You need to provide the TED Talk ID as an argument.

### --lang LANG
Specify the language code for subtitles. The default is 'en' for English.

### --download-all
This option combines the --download-meta and --download-details steps, fetching all available data and subtitles for the talks.

### --download-stats
Calculate and display download success statistics for summaries and subtitles.

### --download-audio {low,medium,high}
Convert the meta.csv file into a download list file (download_<quality>.lst) for the specified audio quality. Choose from 'low', 'medium', or 'high'. This creates an intermediate file with download links that can be used with external download tools.

#### Intermediate File
When using the --download-audio option, the script generates an intermediate file named `download_{quality}.lst`, where {quality} is replaced by the specified quality option (low, medium, or high). For example:

- `python fetch.py --download-audio low` creates `download_low.lst`
- `python fetch.py --download-audio medium` creates `download_medium.lst`
- `python fetch.py --download-audio high` creates `download_high.lst`

This .lst file contains a list of download URLs for the audio files of the specified quality, with one URL per line. You can use this file with external download tools to batch download the audio files.

## Examples

1. To fetch meta data:
   ```
   python fetch.py --download-meta
   ```

2. To download details and subtitles after fetching meta data:
   ```
   python fetch.py --download-details
   ```

3. To download subtitles for a specific talk (replace 12345 with the actual TED Talk ID):
   ```
   python fetch.py --download-subtitles 12345
   ```

4. To download all data and calculate statistics:
   ```
   python fetch.py --download-all
   python fetch.py --download-stats
   ```

5. To create a download list for high-quality audio:
   ```
   python fetch.py --download-audio high
   ```

Remember to run these commands from the directory containing the script, and ensure you have the required dependencies installed.

## Contributions
I welcome contributions to this project. Please feel free to fork this repository and submit a pull request.
Email me at [wanguolin@gmail.com](mailto:wanguolin@gmail.com) if you have any questions.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
