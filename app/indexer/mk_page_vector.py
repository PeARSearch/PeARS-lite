# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
import os
import json
import numpy as np
import string
from app import db
from app import SPM_EXPERIMENTAL, SPM_EXPERIMENTAL_PATH, spm_model_path, do_pretokenization, pretok_path, add_posttok_eof
import subprocess
from app.api.models import Urls, installed_languages, sp
from app.indexer.htmlparser import extract_html
from app.indexer.vectorizer import vectorize_scale
from app.utils import convert_to_string, convert_dict_to_string, normalise
from scipy.sparse import csr_matrix, vstack, save_npz, load_npz
from os.path import dirname, join, realpath, isfile


dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')

_transformed_word_cache = {}

def pretokenize(text, strategy="interpolate", min_subword_len=5, min_freq=50, bof_placeholder="##$", eof_placeholder="$##"):

    def interpolate(word, n=5):
        res = ""
        i = 0
        for c in word:
            i = (i + 1) % n
            if i == 0:
                res += "$$"
            res += c
        return res


    if strategy != "interpolate":
        raise ValueError("Only pretokenization strategy currently available is 'interpolate'")

    pretok_vocab_path = f"{pretok_path}.vocab_dict.json" 
    with open(pretok_vocab_path, encoding="utf-8") as f:
        pretok_vocab = json.load(f)
    
    words_by_length = sorted(pretok_vocab.keys(), key=lambda w: len(w), reverse=False)
    words_by_length = [w for w in words_by_length if len(w) >= min_subword_len and pretok_vocab[w] > min_freq]
    words_to_len_index = {}
    for i, w in enumerate(words_by_length):
        words_to_len_index[w] = i

    lines_out = []

    if not _transformed_word_cache:
        transformed_words_path = f"{pretok_path}.transform_dict.json"
        with open(transformed_words_path, encoding="utf-8") as f:
            transformed_words = json.load(f)
            _transformed_word_cache.update(transformed_words)

    for line_in in text.split("\n"):
        line_in = line_in.rstrip(os.linesep)
        line_words = set()

        # find all words and assign unique IDs
        for word in re.findall(r"\b(\w+)\b", line_in):
            if word in words_to_len_index and word not in _transformed_word_cache:
                # go through all words shorter than the current one, find the shortest one that matches with the beginning of the current word, and break it up into small pieces
                len_index = words_to_len_index[word]
                w_t = word
                for w in words_by_length[:len_index]:
                    if word.startswith(w):
                        w_t = w_t.replace(w, interpolate(w))
                        break
                _transformed_word_cache[word] = w_t
            line_words.add(word)

        line_t = re.sub(r"\b(\w+)\b", bof_placeholder + r"\1" + eof_placeholder, line_in)
        for lw in line_words:
            w_t = _transformed_word_cache[lw] if lw in words_to_len_index else lw
            line_t = line_t.replace(f"{bof_placeholder}{lw}{eof_placeholder}", w_t)    

        lines_out.append(line_t)

    return "\n".join(lines_out)


def add_eofs(text=None, tokens=None):
    assert text or tokens
    if text:
        tokens = text.split(" ")
    tokens_mod = []
    
    for i, tok in enumerate(tokens):
        # punctuation etc -> don't add EOF sybol 
        if not re.match(r"^▁?\w", tok):
            tokens_mod.append(tok)
        elif i + 1 < len(tokens):  # if there's a next token: add EOF if next token starts with space or is punctuation 
            next_token = tokens[i + 1]
            if next_token.startswith("▁") or re.match(r"^\W", next_token):
                tokens_mod.append(f"{tok}▁")
            else:
                tokens_mod.append(tok)

        else:  # end of the text: always append EOF
            tokens_mod.append(f"{tok}▁")

    return " ".join(tokens_mod)


def _tokenize_via_system_call(text):
    proc = subprocess.Popen([f"{SPM_EXPERIMENTAL_PATH}/build/src/spm_encode", f"--model={spm_model_path}"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return (
        proc.communicate(text.encode("utf-8"))
        [0]
        .decode("utf-8")
        .strip()
    )


def tokenize_text(lang, text):

    if do_pretokenization:
        text = pretokenize(text)            

    if SPM_EXPERIMENTAL:
        text = _tokenize_via_system_call(text.lower())
    else:
        text = ' '.join([wp for wp in sp.encode_as_pieces(text.lower())])
    if add_posttok_eof:
        text = add_eofs(text)

    print("TOKENIZED",text)
    return text


def compute_vec(lang, text, pod_m):
    v = vectorize_scale(lang, text, 5, pod_m.shape[1]) # log prob power 5, top words = pod_m.shape[1] todo
    pod_m = vstack((pod_m,csr_matrix(v)))
    print("VEC",v,pod_m.shape)
    return pod_m


# def compute_vectors(target_url, keyword, lang):
#     print("Computing vectors for", target_url, "(",keyword,")",lang)
#     print(pod_dir)
#     pod_m = load_npz(join(pod_dir,keyword+'.npz'))
#     if not db.session.query(Urls).filter_by(url=target_url).all():
#         u = Urls(url=target_url)
#         title, body_str, snippet, cc, error = extract_html(target_url)
#         if error is None and snippet != '':
#             text = title + " " + body_str
#             text = tokenize_text(lang, text)
#             pod_m = compute_vec(lang, text, pod_m)
#             u.title = str(title)
#             u.vector = str(pod_m.shape[0]-1)
#             u.keyword = keyword
#             u.pod = keyword
#             u.snippet = str(snippet)
#             if cc:
#                 u.cc = True
#             #print(u.url,u.title,u.vector,u.snippet,u.cc,u.pod)
#             db.session.add(u)
#             db.session.commit()
#             save_npz(join(pod_dir,keyword+'.npz'),pod_m)
#             podsum = np.sum(pod_m, axis=0)
#             return True, podsum
#         else:
#             if snippet == '':
#                 print("IGNORING URL: Snippet empty.")
#             else:
#                 print(error)
#             return False, None
#     else:
#         return True, None


def compute_vectors_local_docs(target_url, title, snippet, description, doc, keyword, lang):
    cc = False
    pod_m = load_npz(join(pod_dir,keyword+'.npz'))
    if not db.session.query(Urls).filter_by(title=title, pod=keyword).all():
        print("Computing vectors for", target_url, "(",keyword,")",lang)
        u = Urls(url=target_url)
        text = title + " " + description + " " + doc
        #print(text)
        text = tokenize_text(lang, text)
        pod_m = compute_vec(lang, text, pod_m)
        u.title = title
        u.snippet = snippet
        u.description = description[:100]
        u.vector = str(pod_m.shape[0]-1)
        u.keyword = keyword
        u.pod = keyword
        u.cc = cc
        db.session.add(u)
        db.session.commit()
        save_npz(join(pod_dir,keyword+'.npz'),pod_m)
    podsum = np.sum(pod_m, axis=0)
    return True, podsum


def compute_query_vectors(query, lang):
    """ Make distribution for query """
    #query = query.rstrip('\n')
    #words = query.split()
    text = tokenize_text(lang, query)
    print(text)
    v = vectorize_scale(lang, text, 5, len(text)) #log prob power 5
    print(csr_matrix(v))
    return v
