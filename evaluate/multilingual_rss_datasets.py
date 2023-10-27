import os
import re
import json
import shutil
import argparse
import datetime
import time
import random

import pandas as pd
import feedparser
from newsplease import NewsPlease

random.seed(1996)

MAX_ARCHIVE_SIZE = 1_000_000


def remove_html(string):
    if not string:
        return string

    return re.sub(r"<.*?>", "", string)


def get_new_records(known_urls, domain="news", language="it"):
    new_records = []
    with open(f"feeds_{domain}.json", encoding="utf-8") as f:
        feeds_to_watch = json.load(f)

    feeds_and_links = list(feeds_to_watch[language].items())
    random.shuffle(feeds_and_links)
    for feed_name, feed_link in feeds_and_links:
        if feed_link.startswith("COLLECTION::"):
            collection_file = feed_link.replace("COLLECTION::", "")
            with open(collection_file, "r") as f:
                subfeeds = json.load(f)
        else:
            subfeeds = {feed_name: feed_link}

        for sub_name, sub_link in subfeeds.items():
            if sub_name != feed_name:
                sub_name = f"{feed_name} ({sub_name})".lower()

            print(f"Crawling feed: {sub_name}")
            feed = feedparser.parse(sub_link)
            for entry in feed["entries"]:
                if entry["link"] in known_urls:
                    continue
                if len(new_records) + len(known_urls) >= MAX_ARCHIVE_SIZE:
                    print("\tMaximum archive limit reached, quitting...")
                    break
                article = NewsPlease.from_url(entry["link"])
                if entry.get("published_parsed"):
                    time_stamp = pd.Timestamp(time.mktime(entry["published_parsed"]), unit="s")
                else:
                    time_stamp = None
                try:
                    new_records.append({
                        "link": entry["link"],
                        "feed": sub_name,
                        "pubdate_timestamp": time_stamp,
                        "pubdate_string": entry.get("published"),
                        "title": entry.get("title"),
                        "description": article.description if article.description is not None else remove_html(entry.get("description")),
                        "body_text": article.maintext
                    })
                except Exception as e:
                    print(f"Could not process article: {entry['link']}")
                    print(e)
                    print()
    return pd.DataFrame(new_records)


def scrape(domain="news"):

    for language in ["sl", "ru", "fr"]:
        records_file = f"crawled_news/{language}_{domain}.jsonl"
        if os.path.isfile(records_file):
            existing_records = pd.read_json(records_file, orient="records", lines=True)
            known_urls = set(existing_records["link"].to_list())
        else:
            existing_records = None
            known_urls = set()

        new_records = get_new_records(known_urls, language=language, domain=domain)
        final_records = pd.concat([existing_records, new_records], axis=0).reset_index(drop=True)
        if len(final_records) > 0:
            final_records.to_json(records_file, orient="records", lines=True)
        with open(f"crawled_news/logs_{language}_{domain}.txt", "a", encoding="utf-8") as log_f:
            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_f.write(f"[{time_stamp}] added {len(new_records)} records, new total: {len(final_records)}" + os.linesep)


def process(sample_size=0, domain="news"):

    for language in ["sl", "ru", "fr"]:
        records_file = f"crawled_news/{language}_{domain}.jsonl"
        if not os.path.isfile(records_file):
            print(f"Records file {records_file} not found, skipping...")
            continue

        if sample_size:
            out_dir = f"crawled_news/txt_{language}_{domain}_sample{sample_size}"
        else:
            out_dir = f"crawled_news/txt_{language}_{domain}"
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        os.mkdir(out_dir)

        records = pd.read_json(records_file, orient="records", lines=True)
        if sample_size > 0:
            records = records.sample(sample_size)

        for idx, row in records.iterrows():
            out_file = f"{out_dir}/{idx}_{row['feed']}{row['pubdate_timestamp']}.txt"
            with open(out_file, "w", encoding="utf-8") as fo:
                fo.write((row["title"] or "") + os.linesep)
                fo.write((row["description"] or "") + os.linesep)
                fo.write((row["body_text"] or "") + os.linesep)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["scrape", "process"])
    ap.add_argument("--domain", choices=["news", "recipes"], default="news")
    ap.add_argument("--process_sample_size", type=int, default=0)
    args = ap.parse_args()

    if args.action == "scrape":
        scrape(domain=args.domain)
    else:
        process(sample_size=args.process_sample_size, domain=args.domain)