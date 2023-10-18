import os
import re
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

FEEDS_TO_WATCH = {
    "fr": {
        "franceinfo-politics": "https://www.francetvinfo.fr/politique.rss",
        "franceinfo-society": "https://www.francetvinfo.fr/societe.rss",
        "franceinfo-fait-divers": "https://www.francetvinfo.fr/faits-divers.rss",
        "franceinfo-justice": "https://www.francetvinfo.fr/societe/justice.rss",
        "franceinfo-africa": "https://www.francetvinfo.fr/monde/afrique.rss",
        "franceinfo-americas": "https://www.francetvinfo.fr/monde/ameriques.rss",
        "franceinfo-asia": "https://www.francetvinfo.fr/monde/asie.rss",
        "franceinfo-europe": "https://www.francetvinfo.fr/monde/europe.rss",
        "franceinfo-near-east": "https://www.francetvinfo.fr/monde/proche-orient.rss",
        "franceinfo-environment": "https://www.francetvinfo.fr/monde/environnement.rss",
        
        "france24-world": "https://www.france24.com/fr/rss",
        "france24-europe": "https://www.france24.com/fr/europe/rss",
        "france24-france": "https://www.france24.com/fr/france/rss",
        "france24-africa": "https://www.france24.com/fr/afrique/rss",
        "france24-middle-east": "https://www.france24.com/fr/moyen-orient/rss",
        "france24-americas": "https://www.france24.com/fr/ameriques/rss",
        "france24-asia-pacific": "https://www.france24.com/fr/asie-pacifique/rss",

        "rtbf-news": "https://rss.rtbf.be/article/rss/highlight_rtbf_info.xml?source=internal",
        "rtbf-liege": "http://rss.rtbf.be/article/rss/highlight_rtbfinfo_regions-liege.xml?source=internal",
        "rtbf-living-here": "https://rss.rtbf.be/article/rss/highlight_vivacite_vivre-ici.xml?source=internal",
        "rtbf-sport": "https://rss.rtbf.be/article/rss/highlight_rtbf_sport.xml?source=internal",
        "rtbf-practical-life": "https://rss.rtbf.be/article/rss/highlight_rtbf_vie-pratique.xml?source=internal",
        "rtbf-science-technology": "https://rss.rtbf.be/article/rss/highlight_rtbf_sciences-et-technologies.xml?source=internal",
        "rtbf-environment-nature": "https://rss.rtbf.be/article/rss/highlight_rtbf_environnement-et-nature.xml?source=internal",
        "rtbf-health-wellbeing": "https://rss.rtbf.be/article/rss/highlight_rtbf_sante-et-bien-etre.xml?source=internal",

        "radio-canada-home": "https://ici.radio-canada.ca/rss/1000524",
        "radio-canada-main-stories": "https://ici.radio-canada.ca/rss/4159",
        "radio-canada-continuous": "https://ici.radio-canada.ca/rss/1000524",
        "radio-canada-nutrition": "https://ici.radio-canada.ca/rss/7239",
        "radio-canada-art-of-life": "https://ici.radio-canada.ca/rss/4163",
        "radio-canada-economy": "https://ici.radio-canada.ca/rss/5717",
        "radio-canada-environment": "https://ici.radio-canada.ca/rss/92408",
        "radio-canada-international": "https://ici.radio-canada.ca/rss/96",
        "radio-canada-justice-crime": "https://ici.radio-canada.ca/rss/92411",
        "radio-canada-politics": "https://ici.radio-canada.ca/rss/92411",
        "radio-canada-health": "https://ici.radio-canada.ca/rss/4171",
        "radio-canada-science": "https://ici.radio-canada.ca/rss/4165",
        "radio-canada-society": "https://ici.radio-canada.ca/rss/7110",
        "radio-canada-technology": "https://ici.radio-canada.ca/rss/4169",
        "radio-canada-football": "https://ici.radio-canada.ca/rss/1000057",
        "radio-canada-sports-main-headlines": "https://ici.radio-canada.ca/rss/771",
        "radio-canada-hockey": "https://ici.radio-canada.ca/rss/1000056",
        "radio-canada-olympics": "https://ici.radio-canada.ca/rss/64852",
        "radio-canada-sports-podium": "https://ici.radio-canada.ca/rss/555082",
        "radio-canada-soccer": "https://ici.radio-canada.ca/rss/1000058",
        "radio-canada-tennis": "https://ici.radio-canada.ca/rss/1000059",

        "bbc-afrique-homepage": "https://www.bbc.com/afrique/index.xml",
        "bbc-afrique-africa": "https://www.bbc.com/afrique/region/index.xml",
        "bbc-afrique-world": "https://www.bbc.com/afrique/monde/index.xml",
        "bbc-afrique-sport": "https://www.bbc.com/afrique/sports/index.xml",

        "france-blue-alsace-news": "https://www.francebleu.fr/rss/alsace/rubrique/infos.xml",
        "france-blue-alsace-sport": "https://www.francebleu.fr/rss/alsace/rubrique/sports.xml",
        "france-blue-alsace-culture": "https://www.francebleu.fr/rss/alsace/rubrique/culture.xml",
        "france-blue-alsace-daily-life": "https://www.francebleu.fr/rss/alsace/rubrique/vie-quotidienne.xml",

        "france-blue-armorique-news": "https://www.francebleu.fr/rss/armorique/rubrique/infos.xml",
        "france-blue-armorique-sport": "https://www.francebleu.fr/rss/armorique/rubrique/sports.xml",
        "france-blue-armorique-culture": "https://www.francebleu.fr/rss/armorique/rubrique/culture.xml",
        "france-blue-armorique-daily-life": "https://www.francebleu.fr/rss/armorique/rubrique/vie-quotidienne.xml",

        "france-blue-auxerre-news": "https://www.francebleu.fr/rss/auxerre/rubrique/infos.xml",
        "france-blue-auxerre-sport": "https://www.francebleu.fr/rss/auxerre/rubrique/sports.xml",
        "france-blue-auxerre-culture": "https://www.francebleu.fr/rss/auxerre/rubrique/culture.xml",
        "france-blue-auxerre-daily-life": "https://www.francebleu.fr/rss/auxerre/rubrique/vie-quotidienne.xml",

        "france-blue-azur-news": "https://www.francebleu.fr/rss/azur/rubrique/infos.xml",
        "france-blue-azur-sport": "https://www.francebleu.fr/rss/azur/rubrique/sports.xml",
        "france-blue-azur-culture": "https://www.francebleu.fr/rss/azur/rubrique/culture.xml",
        "france-blue-azur-daily-life": "https://www.francebleu.fr/rss/azur/rubrique/vie-quotidienne.xml",

        "france-blue-bearn-news": "https://www.francebleu.fr/rss/bearn/rubrique/infos.xml",
        "france-blue-bearn-sport": "https://www.francebleu.fr/rss/bearn/rubrique/sports.xml",
        "france-blue-bearn-culture": "https://www.francebleu.fr/rss/bearn/rubrique/culture.xml",
        "france-blue-bearn-daily-life": "https://www.francebleu.fr/rss/bearn/rubrique/vie-quotidienne.xml",

        "france-blue-belfort-montbeliard-news": "https://www.francebleu.fr/rss/belfort-montbeliard/rubrique/infos.xml",
        "france-blue-belfort-montbeliard-sport": "https://www.francebleu.fr/rss/belfort-montbeliard/rubrique/sports.xml",
        "france-blue-belfort-montbeliard-culture": "https://www.francebleu.fr/rss/belfort-montbeliard/rubrique/culture.xml",
        "france-blue-belfort-montbeliard-daily-life": "https://www.francebleu.fr/rss/belfort-montbeliard/rubrique/vie-quotidienne.xml",

        "france-blue-besancon-news": "https://www.francebleu.fr/rss/besancon/rubrique/infos.xml",
        "france-blue-besancon-sport": "https://www.francebleu.fr/rss/besancon/rubrique/sports.xml",
        "france-blue-besancon-culture": "https://www.francebleu.fr/rss/besancon/rubrique/culture.xml",
        "france-blue-besancon-daily-life": "https://www.francebleu.fr/rss/besancon/rubrique/vie-quotidienne.xml",

        "france-blue-bourgogne-news": "https://www.francebleu.fr/rss/bourgogne/rubrique/infos.xml",
        "france-blue-bourgogne-sport": "https://www.francebleu.fr/rss/bourgogne/rubrique/sports.xml",
        "france-blue-bourgogne-culture": "https://www.francebleu.fr/rss/bourgogne/rubrique/culture.xml",
        "france-blue-bourgogne-daily-life": "https://www.francebleu.fr/rss/bourgogne/rubrique/vie-quotidienne.xml",

        "france-blue-breizh-izel-news": "https://www.francebleu.fr/rss/breizh-izel/rubrique/infos.xml",
        "france-blue-breizh-izel-sport": "https://www.francebleu.fr/rss/breizh-izel/rubrique/sports.xml",
        "france-blue-breizh-izel-culture": "https://www.francebleu.fr/rss/breizh-izel/rubrique/culture.xml",
        "france-blue-breizh-izel-daily-life": "https://www.francebleu.fr/rss/breizh-izel/rubrique/vie-quotidienne.xml",

    },

    "ru": {
        "meduza-news": "https://meduza.io/rss/news",
        "meduza-fun":"https://meduza.io/rss/fun",
        "moscowtimes-news":"https://www.moscowtimes.ru/rss/news",
        "moscowtimes-opinion": "https://www.moscowtimes.ru/rss/opinion",
        "moscowtimes-financial":"https://www.moscowtimes.ru/rss/ft",
        "novayagazeta-eu": "https://novayagazeta.eu/feed/rss",
        "belsat-ru": "https://belsat.eu/rss-ru.xml",

        "bbc-russian": "https://feeds.bbci.co.uk/russian/rss.xml",
        "euronews-russian": "https://ru.euronews.com/rss",
        "dw-russian-home": "https://rss.dw.com/rdf/rss-ru-all",
        "dw-russian-news": "http://rss.dw.de/xml/rss-ru-news",
        "dw-russian-politics": "http://rss.dw.de/xml/rss-ru-pol",
        "dw-russian-economy": "http://rss.dw.de/xml/rss-ru-eco",
        "dw-russian-cars": "http://rss.dw.de/xml/rss-ru-auto",
        "dw-russian-culture": "http://rss.dw.de/xml/rss-ru-cul",
        "dw-russian-russia": "http://rss.dw.de/atom/rss-ru-rus",
        "dw-russian-germany": "http://rss.dw.de/xml/rss-ru-ger",
        "dw-russian-europe": "http://rss.dw.de/xml/rss-ru-eu",
        "dw-russian-belarus": "http://rss.dw.de/xml/rss-ru-bel",
        
        "rfi-russian": "https://www.rfi.fr/ru/rss",

        "vox-america-ru-home": "https://www.golosameriki.com/api/zkroqremuoqq",
        "vox-america-ru-current": "https://www.golosameriki.com/api/zkj_vemyyt",
        "vox-america-ru-news": "https://www.golosameriki.com/api/zkivremjvq",
        "vox-america-ru-ukraine": "https://www.golosameriki.com/api/zub_oeptyp",
        "vox-america-ru-usa": "https://www.golosameriki.com/api/zjj_reyyyo",
        "vox-america-ru-us-in-a-minute": "https://www.golosameriki.com/api/zt-yteivvt",
        "vox-america-ru-us-elections": "https://www.golosameriki.com/api/zurtqqeputqq",
        "vox-america-ru-interview": "https://www.golosameriki.com/api/zj-_veyvyt",
        "vox-america-ru-russia": "https://www.golosameriki.com/api/zib_pejvy_",
        "vox-america-ru-belarus": "https://www.golosameriki.com/api/zr-_peuyym",
        "vox-america-ru-georgia": "https://www.golosameriki.com/z/1615",
        "vox-america-ru-world": "https://www.golosameriki.com/api/zgj_te_yyq",
        "vox-america-ru-hotspots": "https://www.golosameriki.com/z/1942",
        "vox-america-ru-expertise": "https://www.golosameriki.com/api/z-j_qevyyi",
        "vox-america-ru-economy": "https://www.golosameriki.com/api/zp-_ve-yyt",

        "knopka-canada": "https://news.knopka.ca/rss",

        "ua-pravda-main": "https://www.pravda.com.ua/rus/rss/",
        "ua-pravda-news": "https://www.pravda.com.ua/rus/rss/view_news/",
        "ua-pravda-top-stories": "https://www.pravda.com.ua/rus/rss/view_mainnews/",
        
    },
    "sl": {
        "rtv-slovenija-home": "https://www.rtvslo.si/feeds/00.xml",
        "rtv-slovenija-slovenia": "https://img.rtvslo.si/feeds/01.xml",
        "rtv-slovenija-world": "https://www.rtvslo.si/feeds/02.xml",
        "rtv-slovenija-european-union": "https://img.rtvslo.si/feeds/16.xml",
        "rtv-slovenija-economy": "https://www.rtvslo.si/feeds/04.xml",
        "rtv-slovenija-crime": "https://www.rtvslo.si/feeds/08.xml",
        "rtv-slovenija-environment": "https://www.rtvslo.si/feeds/12.xml",
        "rtv-slovenija-science-technology": "https://www.rtvslo.si/feeds/09.xml",
        "rtv-slovenija-sport": "https://www.rtvslo.si/feeds/03.xml",
        "rtv-slovenija-culture": "https://www.rtvslo.si/feeds/05.xml",
        "rtv-slovenija-entertainment": "https://www.rtvslo.si/feeds/06.xml",
        "rtv-slovenija-adventure-tours": "https://www.rtvslo.si/feeds/28.xml",

        "sta-news": "https://www.sta.si/rss-0",
        "sta-slovenia": "https://www.sta.si/rss-1",
        "sta-news": "https://www.sta.si/rss-2",
        "sta-economy": "https://www.sta.si/rss-3",
        "sta-sport": "https://www.sta.si/rss-4",
        "sta-culture": "https://www.sta.si/rss-5",
        "sta-interests": "https://www.sta.si/rss-6",
        "sta-traffic": "https://www.sta.si/rss-13",

        "delo-newspaper": "https://www.delo.si/rss/",
        "slovenske-novice": "https://www.slovenskenovice.si/rss",
        "dnevnik": "https://www.dnevnik.si/rss",
        "zurnal24": "https://www.zurnal24.si/feeds/latest",
        "24ur": "https://www.24ur.com/rss",

        "siol-news": "https://siol.net/feeds/section/novice",
        "siol-news-slovenia": "https://siol.net/feeds/section/novice/slovenija",
        "siol-news-business": "https://siol.net/feeds/section/posel-danes",
        "siol-news-business-legal": "https://siol.net/feeds/section/posel-danes/pravni-nasvet",
        "siol-news-personal-finance": "https://siol.net/feeds/section/posel-danes/osebne-finance",
        "siol-news-dream-career": "https://siol.net/posel-danes/sanjska-sluzba"     
    }
} 

def get_new_records(known_urls, language="it"):
    new_records = []
    for feed_name, feed_link in FEEDS_TO_WATCH[language].items():
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
                        "description": article.description,
                        "body_text": article.maintext
                    })
                except Exception as e:
                    print(f"Could not process article: {entry['link']}")
                    print(e)
                    print()
    return pd.DataFrame(new_records)


def scrape():

    for language in ["sl", "ru", "fr"]:
        records_file = f"crawled_news/{language}.jsonl"
        if os.path.isfile(records_file):
            existing_records = pd.read_json(records_file, orient="records", lines=True)
            known_urls = set(existing_records["link"].to_list())
        else:
            existing_records = None
            known_urls = set()

        new_records = get_new_records(known_urls, language=language)
        final_records = pd.concat([existing_records, new_records], axis=0).reset_index(drop=True)
        final_records.to_json(records_file, orient="records", lines=True)
        with open(f"crawled_news/logs_{language}.txt", "a", encoding="utf-8") as log_f:
            time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_f.write(f"[{time_stamp}] added {len(new_records)} records, new total: {len(final_records)}" + os.linesep)


def process(sample_size=0):

    for language in ["sl", "ru", "fr"]:
        records_file = f"crawled_news/{language}.jsonl"
        assert os.path.isfile(records_file)

        if sample_size:
            out_dir = f"crawled_news/txt_{language}_sample{sample_size}"
        else:
            out_dir = f"crawled_news/txt_{language}"
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
    ap.add_argument("--process_sample_size", type=int, default=0)
    args = ap.parse_args()

    if args.action == "scrape":
        scrape()
    else:
        process(args.process_sample_size)