# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import webbrowser
from urllib.parse import urlparse
import re
import math
from app.api.models import Urls, Pods
from app import db
from app.utils_db import (
    get_db_url_snippet, get_db_url_title, get_db_url_cc, get_db_url_pod, get_db_url_notes)

from .overlap_calculation import score_url_overlap, generic_overlap, completeness
from app.search import term_cosine
from app.utils import cosine_similarity, hamming_similarity, convert_to_array, get_language
from app.indexer.mk_page_vector import compute_query_vectors
from scipy.sparse import csr_matrix, load_npz
from scipy.spatial import distance
from os.path import dirname, join, realpath, isfile
import numpy as np

dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')

def score(query, query_dist, kwd):
    URL_scores = {}
    snippet_scores = {}
    DS_scores = {}
    completeness_scores = {}
    pod_m = load_npz(join(pod_dir,kwd+'.npz'))
    m_cosines = 1 - distance.cdist(query_dist, pod_m.todense(), 'cosine')
    m_completeness = completeness(query_dist, pod_m.todense())

    for u in db.session.query(Urls).filter_by(pod=kwd).all():
        DS_scores[u.url] = m_cosines[0][int(u.vector)]
        completeness_scores[u.url] = m_completeness[0][int(u.vector)]
        #URL_scores[u.url] = score_url_overlap(query, u.url)
        snippet_scores[u.url] = generic_overlap(query, u.snippet)
    return DS_scores, completeness_scores, snippet_scores


def score_pods(query, query_dist, lang):
    '''Score pods for a query'''
    pod_scores = {}
    score_sum = 0.0
    podsum = load_npz(join(pod_dir,'podsum.npz'))
    m_cosines = 1 - distance.cdist(query_dist, podsum.todense(), 'cosine')

    pods = db.session.query(Pods).filter_by(language=lang).filter_by(registered=True).all()
    for p in pods:
        score = m_cosines[0][int(p.DS_vector)]
        if math.isnan(score):
            score = 0
        pod_scores[p.name] = score
        score_sum += score
    print("POD SCORES:",pod_scores)
    '''If all scores are rubbish, search entire pod collection
    (we're desperate!)'''
    if score_sum < 0.9: #FIX FOR FRUIT FLY VERSION
        return list(pod_scores.keys())
    else:
        best_pods = []
        for k in sorted(pod_scores, key=pod_scores.get, reverse=True):
            if len(best_pods) < 5: 
                print("Appending pod",k)
                best_pods.append(k)
            else:
                break
        return best_pods


def score_docs(query, query_dist, kwd):
    '''Score documents for a query'''
    document_scores = {}  # Document scores
    DS_scores, completeness_scores, snippet_scores = score(query, query_dist, kwd)
    for url in list(DS_scores.keys()):
        if completeness_scores[url] >= 0.75 and snippet_scores[url] >= 0.75:
            print(url,DS_scores[url], completeness_scores[url], snippet_scores[url])
        #document_scores[url] = 0.5*DS_scores[url] + completeness_scores[url] + 0.1*snippet_scores[url]
        document_scores[url] = completeness_scores[url] + snippet_scores[url]
        if math.isnan(document_scores[url]) or completeness_scores[url] < 0.75 or snippet_scores[url] < 0.75:  # Check for potential NaN -- messes up with sorting in bestURLs.
            document_scores[url] = 0
    return document_scores


def bestURLs(doc_scores):
    best_urls = []
    netlocs_used = []  # Don't return 100 pages from the same site
    c = 0
    for w in sorted(doc_scores, key=doc_scores.get, reverse=True):
        loc = urlparse(w).netloc
        if c < 100:
            if doc_scores[w] > 0:
                #if netlocs_used.count(loc) < 10:
                #print(w,doc_scores[w])
                best_urls.append(w)
                netlocs_used.append(loc)
                c += 1
            else:
                break
        else:
            break
    return best_urls


def ddg_redirect(query):
    print("No suitable pages found.")
    duckquery = ""
    for w in query.rstrip('\n').split():
        duckquery = duckquery + w + "+"
    webbrowser.open("https://duckduckgo.com/?q=" + duckquery.rstrip('+'))
    return


def output(best_urls):
    results = []
    pods = []
    if len(best_urls) > 0:
        for u in best_urls:
            results.append([
                u,
                get_db_url_title(u),
                get_db_url_snippet(u),
                get_db_url_cc(u),
                get_db_url_notes(u),
            ])
            pod = get_db_url_pod(u)
            if pod not in pods:
                pods.append(pod)
            # print(results)
    return results, pods


def run(query, pears):
    document_scores = {}
    query, lang = get_language(query)
    q_dist = compute_query_vectors(query, lang)
    best_pods = score_pods(query, q_dist, lang)
    for pod in best_pods:
        document_scores.update(score_docs(query, q_dist, pod))
    best_urls = bestURLs(document_scores)
    return output(best_urls)
