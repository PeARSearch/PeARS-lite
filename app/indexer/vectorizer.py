# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

from app import spm_vocab_path, add_posttok_eof, PROJ_MAT
from collections import OrderedDict
import numpy as np
from scipy.sparse import csr_matrix, vstack
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing

def read_vocab(vocab_file):
    c = 0
    vocab = {}
    reverse_vocab = {}
    logprobs = []
    with open(vocab_file) as f:
        for l in f:
            l = l.rstrip('\n')
            wp = l.split('\t')[0]
            logprob = -(float(l.split('\t')[1]))
            #logprob = log(lp + 1.1)
            if wp in vocab or wp == '':
                continue
            vocab[wp] = c
            reverse_vocab[c] = wp
            logprobs.append(logprob)
            c+=1
    return vocab, reverse_vocab, logprobs

def wta_vectorized(feature_mat, k, percent=True):
    """
    Apply Winner-Takes-All (WTA) operation to each row of a matrix.
    Implemented in a vectorized manner, without a loop over each row.
    WTA is a feature selection technique that retains only the top-k
    values in each row of the feature matrix, setting all other values to zero.

    Args:
        feature_mat (numpy.ndarray): The input feature matrix.
        k (int or float): If `percent` is True (default), `k` specifies the percentage of
            values to retain in each row (e.g., k=40 means retaining the top 40%).
            If `percent` is False, `k` specifies the exact number of top values to retain.
        percent (bool, optional): If True (default), interpret `k` as a percentage, if False,
            interpret `k` as the exact number of values to retain.

    Returns:
        numpy.ndarray: A modified feature matrix after applying the WTA operation.

    Credit: thanks https://stackoverflow.com/a/59405060
    """

    # Example
    # feature_mat = np.array([[1, 0, 4, -2, 6],
    #                         [2, 5, -1, 2, 0]])
    # k = 40, which mean we keep top 40% = 2 largest values
    m, n = feature_mat.shape
    if percent:
        k = int(k * n / 100)

    # get (unsorted) indices of top-k values
    topk_indices = np.argpartition(feature_mat, -k, axis=1)[:, -k:]
    # np.argpartition splits each row into two parts, the left part
    # contains indices of values smaller than the k-th largest value of the row,
    # and the right part contains indices of values larger than the k-th largest value
    # [:, -k:]: select the right parts, i.e. the part contains indices of values larger than
    # the k-th largest value
    # note that this function return indices, not the actual values
    # np.argpartition -> [[3, 0, 1, 2, 4], [2, 4, 3, 0, 1]]
    # [:, -k:] -> [[2, 4], [0, 1]]

    # get k-th value
    rows, _ = np.indices((m, k))
    kth_vals = feature_mat[rows, topk_indices].min(axis=1)
    # now we need the actual k-th largest values in each row
    # this step slices the original matrix, then take the smallest values each row
    # kth_vals -> [4, 2]

    # get boolean mask of values smaller than k-th
    is_smaller_than_kth = feature_mat < kth_vals[:, None]
    # replace mask by 0
    feature_mat[is_smaller_than_kth] = 0
    return feature_mat

def encode_docs(doc_list, vectorizer, logprobs, power, top_words):
    logprobs = np.array([logprob ** power for logprob in logprobs])
    X = vectorizer.fit_transform(doc_list)
    X = X.multiply(logprobs)
    X = wta_vectorized(X.toarray(),top_words,False)
    X = csr_matrix(X)
    return X


def encode_docs_with_projection(doc_list, vectorizer, logprobs, power, top_words):
    logprobs = np.array([logprob ** power for logprob in logprobs])
    X = vectorizer.fit_transform(doc_list)
    X = X.multiply(logprobs)
    X = X.toarray().dot(PROJ_MAT) # global variable
    X = wta_vectorized(X, top_words, False)
    X = csr_matrix(X)
    return X


def read_n_encode_dataset(doc=None, vectorizer=None, logprobs=None, power=None, top_words=None, verbose=False):
    # read
    doc_list = [doc]

    # encode
    X = encode_docs(doc_list, vectorizer, logprobs, power, top_words)
    # X = encode_docs_with_projection(doc_list, vectorizer, logprobs, power, top_words)
    if verbose:
        k = 10
        inds = np.argpartition(X.todense(), -k, axis=1)[:, -k:]
        for i in range(X.shape[0]):
            ks = [list(vectorizer.vocabulary.keys())[list(vectorizer.vocabulary.values()).index(k)] for k in np.squeeze(np.asarray(inds[i]))]
    return X

def init_vectorizer(lang): 
    vocab, reverse_vocab, logprobs = read_vocab(spm_vocab_path)
    if add_posttok_eof:
        vocab = OrderedDict(vocab) # make sure we can rely on the order
        vocab.update({f"{w}▁": v + len(vocab) for w, v in vocab.items()})
        reverse_vocab = {v: w for w, v in vocab.items()}
        logprobs = logprobs + logprobs
    
    vectorizer = CountVectorizer(vocabulary=vocab, lowercase=True, token_pattern='[^ ]+')
    return vectorizer, logprobs

def vectorize(lang, text, logprob_power, top_words):
    '''Takes input file and return vectorized /scaled dataset'''
    vectorizer, logprobs = init_vectorizer(lang)
    dataset = read_n_encode_dataset(text, vectorizer, logprobs, logprob_power, top_words)
    dataset = dataset.todense()
    return np.asarray(dataset)

def scale(dataset):
    #scaler = preprocessing.MinMaxScaler().fit(dataset)
    scaler = preprocessing.Normalizer(norm='l2').fit(dataset)
    return scaler.transform(dataset)

def vectorize_scale(lang, text, logprob_power, top_words):
    dataset = vectorize(lang, text, logprob_power,top_words)
    return scale(dataset)
