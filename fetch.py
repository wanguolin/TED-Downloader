import os
from time import sleep
from bs4 import BeautifulSoup
import pandas as pd
import requests
import argparse
import json

_lang = "en"
_output_folder = "downloads"
_ted_talks_base_url = "https://www.ted.com/talks/"

if not os.path.exists(_output_folder):
    os.makedirs(_output_folder)
    print(f"Created folder: {_output_folder}")
else:
    print(f"Using existing folder: {_output_folder}")
os.chdir(_output_folder)


def fetch_meta():
    url = "https://www.ted.com/talks/quick-list"
    response = requests.get(url)
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

    max_page = get_max_page(pagination)

    print(f"Max Page:{max_page}")
    meta, total_video = [], 0
    for page in range(1, max_page + 1):
        total_video += parse_meta_webpage(f"{url}?page={page}", meta)

    df = pd.DataFrame(meta)
    df.to_csv("meta.csv", index=False)
    print(
        f"\nTotal Videos: {total_video}\nTotal Pages: {max_page}\nSaved To: meta.csv\nDone!"
    )


def parse_meta_webpage(page_url: str, meta=[]):
    page_count = 0
    response = requests.get(page_url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    pagination = soup.find("div", class_="pagination")
    print(".", end="", flush=True)
    rows = soup.find_all("div", class_="row quick-list__row")
    for row in rows:
        download_links = {"Low": None, "Medium": None, "1080p": None}
        download_items = row.find("ul", class_="quick-list__download").find_all("li")
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
                "Title": row.find("div", class_="col-xs-6 title")
                .find("a")
                .text.strip(),
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
        page_count += 1
    return page_count


def convert_detail_link_to_summary_name(link: str):
    if _ted_talks_base_url not in link:
        raise ValueError("Invalid TED Talk link")
    return f"{link.replace(_ted_talks_base_url, '')}.json"


def convert_detail_link_to_subtitle_name(link: str):
    if _ted_talks_base_url not in link:
        raise ValueError("Invalid TED Talk link")
    return f"{link.replace(_ted_talks_base_url, '')}_sub_{_lang}.json"


def fetch_ted_details_from_meta():
    df = pd.read_csv("meta.csv")
    for _, row in df.iterrows():
        summary_filename = convert_detail_link_to_summary_name(row["Details"])
        subtitle_filename = convert_detail_link_to_subtitle_name(row["Details"])
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


def main():
    parser = argparse.ArgumentParser(
        description="A script to fetch TED Talks meta data and details."
    )
    parser.add_help = True
    parser.add_argument(
        "--fetch-meta", action="store_true", help="Fetch meta data from TED Talks"
    )
    parser.add_argument(
        "--fetch-details",
        action="store_true",
        help="Fetch details from TED Talks using local meta data",
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

    args = parser.parse_args()
    if args.lang != "en":
        _lang = args.lang
    if args.fetch_meta:
        fetch_meta()
    elif args.fetch_details:
        fetch_ted_details_from_meta()
    elif args.download_subtitles:
        ted_talk_id = str(args.download_subtitles)
        download_subtitles(ted_talk_id, _lang)


if __name__ == "__main__":
    main()
