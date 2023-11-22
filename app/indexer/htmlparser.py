# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import requests
import justext
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from langdetect import detect
from app.utils import request_url
from app.indexer import detect_open
from app.api.models import installed_languages
from app import LANG, LANGUAGE_CODES

def remove_boilerplates(response, lang):
    text = ""
    print("REMOVING BOILERPLATES FOR LANG",lang,"(",LANGUAGE_CODES[lang],").")
    paragraphs = justext.justext(
        response.content,
        justext.get_stoplist(LANGUAGE_CODES[lang]),
        max_link_density=0.3,
        stopwords_low=0.1,
        stopwords_high=0.3,
        length_low=30,
        length_high=100)
    for paragraph in paragraphs:
        if not paragraph.is_boilerplate:
            text += paragraph.text + " "
    return text


def BS_parse(url):
    bs_obj = None
    try:
        req = requests.get(url, allow_redirects=True, timeout=30)
        req.encoding = 'utf-8'
    except Exception:
        print("ERROR accessing resource", url, "...")
        return bs_obj, req
    bs_obj = BeautifulSoup(req.text, "lxml")
    return bs_obj, req


def extract_links(url):
    links = []
    try:
        req = requests.head(url, timeout=10)
        if "text/html" not in req.headers["content-type"]:
            print("Not a HTML document...")
            return links
    except Exception:
        return links
    bs_obj, req = BS_parse(url)
    if not bs_obj:
        return links
    hrefs = bs_obj.findAll('a', href=True)
    for h in hrefs:
        if h['href'].startswith('http') and '#' not in h['href']:
            links.append(h['href'])
        else:
            links.append(urljoin(url, h['href']))
    return links


def extract_html(url):
    '''From history info, extract url, title and body of page,
    cleaned with BeautifulSoup'''
    title = ""
    body_str = ""
    snippet = ""
    cc = False
    language = LANG
    error = None
    bs_obj, req = BS_parse(url)
    if not bs_obj:
        error = "ERROR extract_html: Failed to get BeautifulSoup object."
        return title, body_str, snippet, cc, error
    if hasattr(bs_obj.title, 'string'):
        if url.startswith('http'):
            title = bs_obj.title.string
            if title is None:
                title = ""
            body_str = remove_boilerplates(req, LANG)
            try:
                language = detect(title + " " + body_str)
                print("Language for", url, ":", language)
            except Exception:
                title = ""
                error = "ERROR extract_html: Couldn't detect page language."
                return title, body_str, snippet, cc, error
            print(body_str)
            if language not in installed_languages:
                error = "ERROR extract_html: language is not supported."
                title = ""
                return title, body_str, snippet, cc, error
            snippet = body_str[:300].replace(',', '-')
    return title, body_str, snippet, cc, error
