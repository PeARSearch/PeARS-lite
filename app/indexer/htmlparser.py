# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import requests
import justext
from urllib.parse import urljoin
from app.indexer import detect_open
from bs4 import BeautifulSoup
from langdetect import detect
from app.api.models import installed_languages

auth_token = "TOK:1234"

def remove_boilerplates(response):
    text = ""
    paragraphs = justext.justext(
        response.content,
        justext.get_stoplist("English"), #FIX FOR MULTIPLE LANGUAGES
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
    req = None
    try:
        req = requests.get(url, allow_redirects=True, timeout=30, headers={'Authorization': auth_token})
        req.encoding = 'utf-8'
    except Exception:
        print("Request failed when trying to index", url, "...")
        return False, req
    if req.status_code != 200:
        logging.exception(
            "Warning: " + str(req.url) + ' has a status code of: ' +
            str(req.status_code) + ' omitted from database.\n')
        return False, req
    bs_obj = BeautifulSoup(req.text, "lxml")
    return bs_obj, req


def extract_links(url):
    links = []
    try:
        req = requests.get(url, timeout=10, headers={'Authorization': auth_token})
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
    error = None
    language = "en"
    try:
        req = requests.head(url, timeout=10)
        if "text/html" not in req.headers["content-type"]:
            print("Not a HTML document, moving to .txt processing...")
            title, body_str, snippet, cc = extract_txt(url)
            return title, body_str, snippet, cc, error
    except Exception:
        error = "IGNORING URL: Not .html or .txt."
        print(error)
        return title, body_str, snippet, cc, error

    bs_obj, req = BS_parse(url)
    if not bs_obj:
        error = "IGNORING URL: Failed to get BeautifulSoup object..."
        print(error)
        return title, body_str, snippet, cc, error
    if hasattr(bs_obj.title, 'string'):
        if url.startswith('http'):
            title = bs_obj.title.string
            if title is None:
                title = ""
            body_str = remove_boilerplates(req)
            try:
                language = detect(title + " " + body_str)
                print("Language for", url, ":", language)
            except Exception:
                error = "IGNORING URL: Could not detect page language"
                print(error)
                return title, body_str, snippet, cc, error

            if language not in installed_languages:
                error = "IGNORING URL: Language is not supported."
                print(error)
                return title, body_str, snippet, cc, error
            try:
                cc = detect_open.is_cc(url, bs_obj)
            except Exception:
                print("Failed to get CC status for", url, "...")
            if cc:
                snippet = body_str[:200].replace(',', '-')
            else:
                snippet = body_str[:100].replace(',', '-')
    return title, body_str, snippet, cc, error


def extract_txt(url):
    title = url.split('/')[-1]
    body_str = ""
    snippet = ""
    cc = False
    language = "en"
    print("EXTRACT",url)
    print("TITLE",title)
    try:
        req = requests.get(url, timeout=10, headers={'Authorization': auth_token})
    except Exception:
        return title, body_str, snippet, cc
    body_str = req.text
    print("BODY",body_str)
    try:
        language = detect(body_str)
        print("Language for", url, ":", language)
    except Exception:
        print("Couldn't detect page language.")
        return title, body_str, snippet, cc

    if language not in installed_languages:
        print("Ignoring", url, "because language is not supported.")
        title = ""
        return title, body_str, snippet, cc
    snippet = body_str[:200].replace(',', '-')
    return title, body_str, snippet, cc
