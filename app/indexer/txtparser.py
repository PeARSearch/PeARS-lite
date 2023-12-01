# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import requests
from urllib.parse import urljoin
from langdetect import detect
from app.api.models import installed_languages
from app import LANG


def extract_from_url(url):
    title = url.split('/')[-1]
    body_str = ""
    snippet = ""
    cc = False
    language = LANG
    try:
        req = requests.get(url, timeout=10, headers={'Authorization': 'TOK:1234'})
    except Exception:
        return title, body_str, snippet, cc
    body_str = req.text
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
