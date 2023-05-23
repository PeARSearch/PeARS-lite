# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import requests
import justext
from urllib.parse import urljoin
from app.indexer import detect_open
from langdetect import detect
from app.api.models import installed_languages

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



def extract_from_url(url):
    title = url.split('/')[-1]
    body_str = ""
    snippet = ""
    cc = False
    language = "en"
    try:
        req = requests.get(url, timeout=10, headers={'Authorization': 'TOK:1234'})
    except Exception:
        return title, body_str, snippet, cc
    body_str = req.text
    print(req.text)
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
