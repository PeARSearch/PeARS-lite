# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import re
import string
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
    v = v.reshape(10000,)
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

