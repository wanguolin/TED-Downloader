import os
from time import sleep
from bs4 import BeautifulSoup
import pandas as pd
import requests
import argparse
import json
import csv
from datetime import datetime
from collections import defaultdict
import uuid
from supabase import create_client, Client
import getpass
from tqdm import tqdm


_lang = "en"
_output_folder = "downloads"
_ted_talks_base_url = "https://www.ted.com/talks/"
_quick_list = "https://www.ted.com/talks/quick-list"
_meta_filename = "meta.csv"

if not os.path.exists(_output_folder):
    os.makedirs(_output_folder)
    print(f"Created folder: {_output_folder}")
else:
    print(f"Using existing folder: {_output_folder}")
os.chdir(_output_folder)


def fetch_meta():
    _quick_list = "https://www.ted.com/talks/quick-list"
    response = requests.get(_quick_list)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    pagination = soup.find("div", class_="pagination")

    def get_max_page(pagination):
        try:
            max_page = int(
                pagination.find_all("a", class_="pagination__item pagination__link")[
                    -1
                ].text
            )
        except (ValueError, IndexError):
            max_page = 1
        return max_page

    meta_exists = pd.DataFrame()
    if os.path.exists(_meta_filename):
        meta_exists = pd.read_csv(_meta_filename)
    first_title = meta_exists["Title"].iloc[0] if not meta_exists.empty else ""
    max_page = get_max_page(pagination)
    print(f"Max Page:{max_page}")
    meta_fetched, total_video = [], 0
    for page in range(1, max_page + 1):
        if (
            parse_meta_webpage(f"{_quick_list}?page={page}", first_title, meta_fetched)
            == False
        ):
            total_video += len(meta_fetched)
            break
        total_video += len(meta_fetched)
    if len(meta_fetched) > 0:
        pd.concat([pd.DataFrame(meta_fetched), meta_exists], ignore_index=True).to_csv(
            _meta_filename, index=False
        )

    print(
        f"\nTotal Videos: {total_video}\nTotal Pages: {max_page}\nSaved To: meta.csv\nDone!"
    )


def parse_meta_webpage(page_url: str, first_title: str, meta=[]) -> bool:
    """
    Parse the TED Talks meta data from the given page URL.
    Args:
        page_url (str): URL of the TED Talks page.
        meta (list): List to store the parsed meta data.
        existing_title (set): Set to store the existing titles.
    Returns:
        If all titles on the page are new (not encountered in existing titles), return True. If any title already exists, return False.
    """
    response = requests.get(page_url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    pagination = soup.find("div", class_="pagination")
    print(".", end="", flush=True)
    rows = soup.find_all("div", class_="row quick-list__row")
    for row in rows:
        download_links = {"Low": None, "Medium": None, "1080p": None}
        download_items = row.find("ul", class_="quick-list__download").find_all("li")
        title = row.find("div", class_="col-xs-6 title").find("a").text.strip()
        if first_title == title:
            return False
        for item in download_items:
            link_text = item.text.strip()
            link_url = item.find("a")["href"]
            if "Low" in link_text:
                download_links["Low"] = link_url
            elif "Medium" in link_text:
                download_links["Medium"] = link_url
            elif "1080p" in link_text:
                download_links["1080p"] = link_url
        meta.append(
            {
                "Published": row.find("div", class_="col-xs-1")
                .find("span", class_="meta")
                .text.strip(),
                "Title": title,
                "Event": row.find("div", class_="col-xs-2 event")
                .find("a")
                .text.strip(),
                "Duration": row.find_all("div", class_="col-xs-1")[-1].text.strip(),
                "download_low": download_links["Low"],
                "download_medium": download_links["Medium"],
                "download_1080p": download_links["1080p"],
                "Details": f"https://www.ted.com{row.find('div', class_='col-xs-6 title').find('a')['href']}",
            }
        )
    return True


def convert_detail_link_to_filenames(link: str, lang: str = _lang) -> tuple[str, str]:
    if _ted_talks_base_url not in link:
        raise ValueError("Invalid TED Talk link")
    
    base_name = link.replace(_ted_talks_base_url, '')
    summary_filename = f"{base_name}.json"
    subtitle_filename = f"{base_name}_sub_{lang}.json"
    
    return summary_filename, subtitle_filename


def fetch_ted_details_from_meta():
    df = pd.read_csv("meta.csv")
    for _, row in df.iterrows():
        summary_filename, subtitle_filename = convert_detail_link_to_filenames(row["Details"])
        if (
            not os.path.exists(summary_filename)
            or os.path.getsize(summary_filename) == 0
        ):
            if download_summary(row["Details"]) == False:
                print(f"Failed to download details for {row['Details']}")
                continue
        with open(summary_filename, "r") as f:
            details = json.load(f)
            ted_talks_id = details.get("ted_talk_id", "")
            if ted_talks_id == "":
                print(f"Failed to get TED Talk ID for {summary_filename}")
                continue
            download_subtitles(
                ted_talks_id,
                _lang,
                subtitle_filename,
            )


def download_subtitles(id: str, lang: str, save_to: str) -> bool:
    url = f"https://www.ted.com/talks/subtitles/id/{id}/lang/{lang}"
    if os.path.exists(save_to):
        print(f"Subtitle already exists: {save_to}")
        return
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print(f"No subtitles found for {id} in {lang}")
            return False
        with open(save_to, "w") as f:
            json.dump(data, f, indent=4)
        return True
    else:
        return False


def download_summary(url: str):
    save_content_to = convert_detail_link_to_summary_name(url)
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if script_tag:
        data = json.loads(script_tag.string)
        ted_talk_id = (
            data.get("props", {})
            .get("pageProps", {})
            .get("videoData", {})
            .get("id", None)
        )
        print(f"TED Talk ID: {ted_talk_id}")
    else:
        print("No script tag with id '__NEXT_DATA__' found.")

    def extract_content(name):
        meta_tag = soup.find("meta", attrs={"name": name})
        if meta_tag:
            return meta_tag.get("content")
        return None

    try:
        with open(save_content_to, "w") as f:
            json.dump(
                {
                    "title": extract_content("title"),
                    "description": extract_content("description"),
                    "keywords": extract_content("keywords"),
                    "author": extract_content("author"),
                    "medium": extract_content("medium"),
                    "ted_talk_id": ted_talk_id,
                },
                f,
                indent=4,
            )
            print(f"Saved to {save_content_to}")
    except Exception as e:
        print(f"Failed to save {save_content_to}: {e}")
        return False


def download_stats():
    print("Updating meta.csv...")
    fetch_meta()
    meta = pd.read_csv("meta.csv")
    total = len(meta)
    summary_successful_downloads = 0
    subtitle_successful_downloads = 0

    for link in meta["Details"]:
        summary_name = convert_detail_link_to_summary_name(link)
        subtitle_name = convert_detail_link_to_subtitle_name(link)

        if os.path.exists(summary_name):
            summary_successful_downloads += 1
        if os.path.exists(subtitle_name):
            subtitle_successful_downloads += 1

    summary_success_rate = (summary_successful_downloads / total) * 100
    subtitle_success_rate = (subtitle_successful_downloads / total) * 100

    print(
        f"Summary Download Success Rate: {summary_successful_downloads}/{total} ({summary_success_rate:.2f}%)"
    )
    print(
        f"Subtitle Download Success Rate: {subtitle_successful_downloads}/{total} ({subtitle_success_rate:.2f}%)"
    )


def download(quality: str):
    if quality not in ["low", "medium", "1080p"]:
        print("Invalid quality specified. Choose from 'low', 'medium', '1080p'.")
        exit(1)
    quality_column_map = {
        "low": "download_low",
        "medium": "download_medium",
        "high": "download_1080p",
    }

    if quality not in quality_column_map:
        raise ValueError(
            "Invalid quality specified. Choose from 'low', 'medium', 'high'."
        )

    column_name = quality_column_map[quality]

    print(f"Processing download list with {quality} quality...")

    input_file = "meta.csv"
    output_file = f"download_{quality}.lst"

    download_links = []
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            value = row.get(column_name)
            if value:
                outfile.write(value + "\n")
                download_links.append(value)


def import_to_supabase(meta_csv_path: str = "meta.csv", supabase_url_override: str = None) -> str:
    def get_details_and_subtitles(details_link: str) -> tuple[dict, dict]:
        def safe_load_json(filename: str) -> dict:
            try:
                with open(filename, "r") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
        details_filename, subtitle_filename = convert_detail_link_to_filenames(details_link)
        details_json, subtitles_json = safe_load_json(details_filename), safe_load_json(subtitle_filename)
        return details_json, subtitles_json
    
    print("Please enter your Supabase credentials:")
    supabase_url = "http://localhost:54321"
    if supabase_url_override is not None:
        supabase_url = supabase_url_override
    supabase_key = getpass.getpass("Supabase Key: ")

    supabase: Client = create_client(supabase_url, supabase_key)

    titles = []
    keywords = defaultdict(int)

    df = pd.read_csv(meta_csv_path)
    df.fillna("", inplace=True)
    max_varchar_size = {
        "title": 0,
        "event": 0,
        "duration": 0,
        "details_link": 0,
    }
    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Importing data"):
        published_date = (
            datetime.strptime(row["Published"], "%b %Y").strftime("%Y-%m-%d")
            if row["Published"]
            else None
        )
        details_json, subtitles_json = get_details_and_subtitles(row["Details"])
        if details_json.get("keywords", None) is not None:
            details_json["keywords"] = [keyword.strip() for keyword in details_json["keywords"].split(", ") if keyword.strip() not in ["TED", "talks"]]
            for keyword in details_json["keywords"]:
                keywords[keyword] += 1
        download_links = {
            "low": row["download_low"],
            "medium": row["download_medium"],
            "1080p": row["download_1080p"],
        }
        title, event, duration, details_link = row['Title'], row['Event'], row['Duration'], row['Details']
        data, count = supabase.table("ted_talks").insert({
            "published": published_date,
            "title": title,
            "event": event,
            "duration": duration,
            "downloads_json": download_links,
            "details_link": details_link,
            "details_json": details_json,
            "subtitles_json": subtitles_json
        }).execute()
        titles.append(title)
        max_varchar_size["title"] = max(max_varchar_size["title"], len(title))
        max_varchar_size["event"] = max(max_varchar_size["event"], len(event))
        max_varchar_size["duration"] = max(max_varchar_size["duration"], len(duration))
        max_varchar_size["details_link"] = max(max_varchar_size["details_link"], len(details_link))

    with open("titles.json", "w") as f:
        json.dump(titles, f, indent=4)
    
    with open("keywords.json", "w") as f:
        json.dump(keywords, f, indent=4)
        
    print(
        f"Titles are saved to titles.json and keywords.json, don't forget to copy it into the targeting folder\n Max varchar size: {max_varchar_size}"
    )

    return "Data import completed successfully"

def main():
    parser = argparse.ArgumentParser(
        description="A script to fetch TED Talks meta data and details."
    )
    parser.add_help = True
    parser.add_argument(
        "--download-meta",
        action="store_true",
        default=False,
        help="Fetch meta data from TED Talks",
    )
    parser.add_argument(
        "--download-details",
        action="store_true",
        help="Fetch detailed JSON files and subtitles from TED Talks using local metadata",
    )
    parser.add_argument(
        "--download-subtitles",
        type=int,
        help="Fetch subtitles from TED Talks using the provided ID",
    )
    parser.add_argument(
        "--lang",
        type=str,
        help="Language code for subtitles, default is en",
    )
    parser.add_argument("--download-all", action="store_true", help="Download them all")
    parser.add_argument(
        "--download-stats",
        action="store_true",
        default=False,
        help="Calculate download success statistics",
    )
    parser.add_argument(
        "--download-audio",
        type=str,
        default=None,
        help="Convert meta.csv into download_<quality>.lst. Default: low quality. Usage: --output-download-list low, medium, high",
    )
    parser.add_argument(
        "--import-supabase",
        nargs="?",
        const=True,
        default=False,
        metavar="URL",
        help="Import meta.csv and json files to Supabase database. Optionally specify a Supabase URL.",
    )

    args = parser.parse_args()
    if args.lang != "en":
        _lang = args.lang
    if args.download_meta:
        fetch_meta()
    elif args.download_details:
        fetch_ted_details_from_meta()
    elif args.download_subtitles:
        ted_talk_id = str(args.download_subtitles)
        download_subtitles(ted_talk_id, _lang)
    elif args.download_stats:
        download_stats()
    elif args.download_all:
        fetch_meta()
        fetch_ted_details_from_meta()
        download_stats()
    elif args.download_audio is not None:
        download(args.download_audio)
    elif args.import_supabase:
        supabase_url = args.import_supabase if isinstance(args.import_supabase, str) else None
        import_to_supabase(supabase_url_override=supabase_url)


if __name__ == "__main__":
    main()
