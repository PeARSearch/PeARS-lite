# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
import numpy as np
import string
from app import db, VEC_SIZE
from app.api.models import Urls, installed_languages, sp
from app.indexer.htmlparser import extract_html
from app.indexer.vectorizer import vectorize_scale
from app.utils import convert_to_string, convert_dict_to_string, normalise
from scipy.sparse import csr_matrix, vstack, save_npz, load_npz
from os.path import dirname, join, realpath, isfile


dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')

def tokenize_text(lang, text):
    sp.load(f'app/api/models/{lang}/{lang}wiki.model')
    tokens = [wp for wp in sp.encode_as_pieces(text.lower())]
    if tokens[-1] == 's': #if plural marker (for English), remove 
        tokens = tokens[:-1]
    text = ' '.join([wp for wp in sp.encode_as_pieces(text.lower())])
    print("TOKENIZED",text)
    return text


def compute_vec(lang, text, pod_m):
    v = vectorize_scale(lang, text, 5, VEC_SIZE) #log prob power 5, top words 100
    pod_m = vstack((pod_m,csr_matrix(v)))
    return pod_m


def compute_vectors(target_url, keyword, lang):
    print("Computing vectors for", target_url, "(",keyword,")",lang)
    print(pod_dir)
    pod_m = load_npz(join(pod_dir,keyword+'.npz'))
    if not db.session.query(Urls).filter_by(url=target_url).all():
        u = Urls(url=target_url)
        title, body_str, snippet, cc, error = extract_html(target_url)
        print("TITLE",title,"SNIPPET",snippet,"CC",cc,"ERROR",error)
        if error is None and snippet != '':
            text = title + " " + body_str
            text = tokenize_text(lang, text)
            print(text)
            pod_m = compute_vec(lang, text, pod_m)
            u.title = str(title)
            u.vector = str(pod_m.shape[0]-1)
            u.keyword = keyword
            u.pod = keyword
            u.snippet = str(snippet)
            u.doctype = 'url'
            print(u.url,u.title,u.vector,u.snippet,u.pod)
            db.session.add(u)
            db.session.commit()
            save_npz(join(pod_dir,keyword+'.npz'),pod_m)
            podsum = np.sum(pod_m, axis=0)
            return True, podsum, text
        else:
            if snippet == '':
                print("IGNORING URL: Snippet empty.")
            else:
                print(error)
            return False, None, None
    else:
        return True, None, None


def compute_vectors_local_docs(target_url, doctype, title, snippet, keyword, lang):
    cc = False
    pod_m = load_npz(join(pod_dir,keyword+'.npz'))
    if not db.session.query(Urls).filter_by(title=title).all():
        print("Computing vectors for", target_url, "(",keyword,")",lang)
        u = Urls(url=target_url)
        text = title + " " + snippet
        text = tokenize_text(lang, text)
        pod_m = compute_vec(lang, text, pod_m)
        u.title = str(title)
        u.vector = str(pod_m.shape[0]-1)
        u.keyword = keyword
        u.pod = keyword
        if snippet != "":
            u.snippet = str(snippet)
        else:
            u.snippet = u.title
        u.doctype = doctype
        print(u.url,u.doctype,u.title,u.vector,u.snippet,u.pod)
        db.session.add(u)
        db.session.commit()
        save_npz(join(pod_dir,keyword+'.npz'),pod_m)
    podsum = np.sum(pod_m, axis=0)
    return True, podsum, text



def compute_query_vectors(query, lang):
    """ Make distribution for query """
    #query = query.rstrip('\n')
    #words = query.split()
    text = tokenize_text(lang, query)
    print(text)
    v = vectorize_scale(lang, text, 5, len(text)) #log prob power 5
    #print(csr_matrix(v))
    return v
