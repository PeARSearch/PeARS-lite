# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org> 
#
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import re
import requests

from bs4 import BeautifulSoup
from math import sqrt
import numpy as np
from urllib.parse import urljoin
from scipy.spatial import distance
from scipy.sparse import csr_matrix, save_npz
from os.path import dirname, join, realpath, isfile
from pathlib import Path
from datetime import datetime
from app import VEC_SIZE, LOCAL_RUN, LANG, CARBON_DIR


def carbon_print(tracker_results, task_name):
    date = datetime.today().strftime('%Y-%m-%d')
    filename = 'carbon.'+date+'.txt'
    with open(join(CARBON_DIR,filename),'a') as f:
        f.write(task_name+': '+str(tracker_results)+'\n')

def _extract_url_and_kwd(line):
    try:
        url, kwd, lang = line.split(';')
        #In case keyword or lang is not given, go back to defaults
        if kwd == '':
            kwd = 'home'
        if lang == '':
            lang = LANG
        return url, kwd, lang
    except:
        print("ERROR: urls_to_index.txt does not have the right format.")
        return None

def readUrls(url_file):
    urls = []
    keywords = []
    langs = []
    errors = False
    with open(url_file) as fd:
        for line in fd:
            matches = _extract_url_and_kwd(line)
            if matches:
                urls.append(matches[0])
                keywords.append(matches[1])
                langs.append(matches[2])
            else:
                errors = True
    return urls, keywords, langs, errors

def readDocs(doc_file):
    urls = []
    titles = []
    snippets = []
    docs = []
    descriptions = []
    with open(doc_file) as df:
        description = ""
        doc = ""
        for l in df:
            l=l.rstrip('\n')
            if l[:4] == "<doc":
                m = re.search('url=\'([^\']*)\'',l)
                url = m.group(1)
                m = re.search('title=\'([^\']*)\'',l)
                title = m.group(1)
            elif "</doc" not in l:
                if "{{DESCRIPTION}}" in l:
                    description = l.replace("{{DESCRIPTION}} ","")
                elif "{{BODY}}" in l:
                    l = l.replace("{{BODY}} ","")
                    doc+=l+' '
                else:
                    doc+=l+' '
            else:
                snippet = doc[:200]
                urls.append(url)
                titles.append(title)
                snippets.append(snippet)
                descriptions.append(description)
                docs.append(description+' '+doc)
                description = ""
                doc = ""
    return urls, titles, snippets, descriptions, docs


def readBookmarks(bookmark_file, keyword):
    print("READING BOOKMARKS")
    urls = []
    bs_obj = BeautifulSoup(open(bookmark_file), "html.parser")
    dt = bs_obj.find_all('dt')
    tag =''
    for i in dt:
        n = i.find_next()
        if n.name == 'h3':
            tag = n.text
            continue
        else:
            if tag == keyword:
                print(f'url = {n.get("href")}')
                print(f'website name = {n.text}')
                urls.append(n.get("href"))
    return urls


def readPods(pod_file):
    pods = []
    f = open(pod_file, 'r')
    for line in f:
        line = line.rstrip('\n')
        pods.append(line)
    f.close()
    return pods


def init_podsum():
    dir_path = dirname(dirname(realpath(__file__)))
    pod_dir = join(dir_path,'app','static','pods')
    print("Create pods directory if needed")
    print(LOCAL_RUN)
    Path(pod_dir).mkdir(exist_ok=True, parents=True)
    print("Making 0 CSR matrix for pod summaries")
    print("POD DIR",pod_dir)
    pod_summaries = np.zeros((1,VEC_SIZE))
    pod_summaries = csr_matrix(pod_summaries)
    save_npz(join(pod_dir,"podsum.npz"), pod_summaries)

def normalise(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def convert_to_string(vector):
    s = ' '.join(str(i) for i in vector)
    return(s)


def convert_to_array(vector):
    # for i in vector.rstrip(' ').split(' '):
    #    print('#',i,float(i))
    return np.array([float(i) for i in vector.split()])


def convert_dict_to_string(dic):
    s = ""
    for k, v in dic.items():
        s += k + ':' + str(v) + ' '
    return s


def convert_string_to_dict(s):
    d = {}
    els = s.rstrip(' ').split()
    for e in els:
        if ':' in e:
            pair = e.split(':')
            if pair[0] != "" and pair[1] != "":
                d[pair[0]] = pair[1]
    return d


def cosine_similarity(v1, v2):
    if len(v1) != len(v2):
        return 0.0
    num = np.dot(v1, v2)
    den_a = np.dot(v1, v1)
    den_b = np.dot(v2, v2)
    return num / (sqrt(den_a) * sqrt(den_b))

def hamming_similarity(v1, v2):
    return 1 - distance.hamming(v1,v2)

def cosine_to_matrix(q, M):
    qsqrt = sqrt(np.dot(q, q))
    if qsqrt == 0:
        return np.zeros(M.shape[0])
    qMdot = np.dot(q, M.T)
    Mdot = np.dot(M, M.T)
    Msqrts = [sqrt(Mdot[i][i]) for i in range(len(Mdot[0]))]
    cosines = []
    for i in range(len(Mdot[0])):
        if Msqrts[i] != 0:
            cosines.append(qMdot[i] / (qsqrt * Msqrts[i]))
        else:
            cosines.append(0)
    return cosines


def sim_to_matrix(dm_dict, vec, n):
    cosines = {}
    c = 0
    for k, v in dm_dict.items():
        try:
            cos = cosine_similarity(vec, v)
            cosines[k] = cos
            c += 1
        except Exception:
            pass
    c = 0
    neighbours = []
    for t in sorted(cosines, key=cosines.get, reverse=True):
        if c < n:
            if t.isalpha():
                print(t, cosines[t])
                neighbours.append(t)
                c += 1
        else:
            break
    return neighbours


def sim_to_matrix_url(url_dict, vec, n):
    cosines = {}
    for k, v in url_dict.items():
        logging.exception(v.url)
        try:
            cos = cosine_similarity(vec, v.vector)
            cosines[k] = cos
        except Exception:
            pass
    c = 0
    neighbours = []
    for t in sorted(cosines, key=cosines.get, reverse=True):
        if c < n:
            # print(t,cosines[t])
            neighbour = [t, url_dict[t].title, url_dict[t].snippet]
            neighbours.append(neighbour)
            c += 1
        else:
            break
    return neighbours


def get_pod_info(url):
    print("Fetching pod", urljoin(url, "api/self/"))
    pod = None
    try:
        r = requests.get(urljoin(url, "api/self/"))
        if r.status_code == 200:
            pod = r.json()
    except Exception:
        print("Problem fetching pod...")
    return pod


def get_language(query):
    lang = LANG #default
    m = re.search('(.*) -(..\s*)$',query)
    if m:
        query = m.group(1)
        lang = m.group(2)
    return query, lang
