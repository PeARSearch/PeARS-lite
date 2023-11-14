# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
import string
from app import VEC_SIZE, vocab, inverted_vocab
from app.indexer.posix import load_posix
import numpy as np
from scipy.spatial.distance import cdist

def jaccard(a, b):
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


def dice(a, b):
    c = a.intersection(b)
    return float(2 * len(c)) / (len(a) + len(b))


def score_url_overlap(query, url):
    url = url.rstrip('/')  # Strip last backslash if there is one
    m = re.search('.*/([^/]+)', url)  # Get last element in url
    if m:
        url = m.group(1)

    # print jaccard(set(query.lower()), set(url.lower()))
    return dice(set(query.lower()), set(url.lower()))

def generic_overlap(q, s):
    '''Overlap between query and another string'''
    q = "".join(l for l in q if l not in string.punctuation)
    s = "".join(l for l in s if l not in string.punctuation)
    q_words = [w[:-1] if w[-1] == 's' else w for w in q.lower().split()] #dealing with English plurals
    s_words = [w[:-1] if w[-1] == 's' else w for w in s.lower().split()]
    return len(list(set(q_words) & set(s_words))) / len(set(q_words))

def dice_overlap(i1, i2):
    '''Dice coefficient between two strings'''
    i1 = "".join(l for l in i1 if l not in string.punctuation)
    i2 = "".join(l for l in i2 if l not in string.punctuation)
    words1 = i1.lower().split()
    words2 = i2.lower().split()
    return dice(set(words1), set(words2))

def completeness(v, m):
    v = v.reshape(VEC_SIZE,)
    idx = np.where(v != 0)
    v_nz = v[idx]
    numcols = v_nz.shape[0]
    v_nz = v_nz.reshape(1,numcols)
    v_nz = np.where(v_nz > 0, 1, 0)

    m_r = np.array(m[:,idx])
    m_r = m_r.reshape(m.shape[0],numcols)
    m_r = np.where(m_r > 0, 1, 0)

    completeness = 1 - cdist(v_nz, m_r, 'hamming')
    return completeness

def posix_score_seq(posl, enforce_subwords=True):
    # remove repeated words
    posl = list(set(posl))

    # only one subword word: perfect score
    if len(posl) == 1 and len(posl[0]) == 1:
        return 1.0
    
    scores = []

    first_tok_pos = posl[0][0].split('|')  # first word -> first subword token -> split 'pos|pos|pos' to list 
    prev_pos = [int(i) for i in first_tok_pos]

    if enforce_subwords:
        prev_subwords = prev_pos  # keep track of the positions of the previous subwords
    else:
        prev_subwords = None

    for word_idx, word_posl in enumerate(posl): # loop over words
        for p_idx, p_str in enumerate(word_posl):  # loop over subwords inside words
            current_pos = [int(i) for i in p_str.split('|')]
            if enforce_subwords:
                if p_idx == 0:
                    prev_subwords = current_pos  # first subword of a word: just get the positions, e.g. `_water` -> [19|55]
                else:
                    # non-initial subword, e.g. `melon` -> [53|56|99]
                    conseq_subwords = []
                    for p in current_pos:
                        for prev_p in prev_subwords:  # compare distances: match 2nd `melon` instance (56-55 = 1), ignore the others 
                            dist = p - prev_p
                            if dist == 1:
                                conseq_subwords.append(p)
                                break
                    if not conseq_subwords:  # none of the positions of current subword is consecutive
                        scores.append(0.0)  # not the entire word is matched -> 0 score for this word
                        break  # we can ignore the rest of the subwords
                    prev_subwords = conseq_subwords

                # if we made it to the last subword, it means the entire word was matched
                if p_idx == len(word_posl) - 1:
                    scores.append(1.0)  # assign a 1.0
                    
            else:
                if word_idx == 0 and p_idx == 0:
                    pass

                pair_scores = _pair_score(prev_pos, current_pos)
                #print("\nPAIR SCORES",scores)
                if pair_scores:
                    scores.extend(pair_scores)
                else:
                    scores.append(1.0)
            prev_pos = current_pos

    if enforce_subwords:
        return np.mean(scores)  # meaning: the fraction of words that were completely matched (= all subwords consecutive)
    else:
        return np.max(scores)  # meaning: 1.0 if there is at least one pair of tokens that is consecutive both in the query and in the document. Otherwise a fraction of this. 

def posix(q, pod_name):
    posindex = load_posix(pod_name)
    print(q.split())
    query_vocab_ids = [vocab.get(wp) for wp in q.split()]
    if any([i is None for i in query_vocab_ids]):
        print("WARNING: there were unknown tokens in the query")
        print(q.split(), query_vocab_ids)
        query_vocab_ids = [i for i in query_vocab_ids if i is not None]

    idx = []
    for w in query_vocab_ids:
        idx.append(set(posindex[w].keys()))        # get docs containing token

    matching_docs = list(set.intersection(*idx))   # intersect doc lists to only retain the docs that contain *all* tokens
    doc_scores = {}
    for doc in matching_docs:
        positions = []
        for w in query_vocab_ids:
            token_str = inverted_vocab[w]
            token_positions = posindex[w][doc]
            #print("TOKEN STR",token_str)
            if token_str.startswith("▁"):
                positions.append((token_positions,))
            else:
                positions[-1] += (token_positions,)
            #print("DOC",doc,"Q WORD", token_str, token_positions)

        final_score = posix_score_seq(positions)
        doc_scores[doc] = final_score
        #print("\nFINAL SCORE FOR DOC", doc, final_score)
    return doc_scores
