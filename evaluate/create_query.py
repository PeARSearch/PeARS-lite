import argparse
import numpy as np
import random
import json
import pathlib

import setuptools.package_index
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import save_npz, load_npz
import joblib
import sys

def construct_count_max(data_in, persona_name, n_gram=1, save_path=None):
    """
    Constructs a count matrix based on persona-specific text data. Count n-gram. Then saves the results.

    Args:
        persona_name (str): Name of the persona for which the count matrix is constructed.
        n_gram (int): Value for n in n-gram feature extraction. Default is 1 (unigrams).
        save_path (str or None): Filepath to save the constructed count matrix and vocabulary. If None, results are not saved.

    Returns:
        None
    """
    path_list = sorted(pathlib.Path(f'{data_in}/{persona_name}/').glob('*.txt'))
    docs = []
    for path in path_list:
        with open(path) as f:
            docs.append(f.read().strip())

    vectorizer = CountVectorizer(ngram_range=(n_gram, n_gram))
    count_mat = vectorizer.fit_transform(docs)
    save_obj = {'vocab': vectorizer.get_feature_names_out(),
                'count_mat': count_mat}
    joblib.dump(save_obj, save_path, compress=True)


def select_query(data_in, query_dir, persona_name, save_path, filter_frequent_2_and_3_token_queries=False):
    """
    Create pairs of query - file paths containing the query.
    """
    path_list = np.array(sorted(pathlib.Path(f'{data_in}/{persona_name}/').glob('*.txt')))

    # 1000 1-token query
    vectorizer_1 = joblib.load(f'{query_dir}/{persona_name}_vectorizer_1.pkl')
    count_mat_1 = vectorizer_1['count_mat']
    vocab_1 = vectorizer_1['vocab']
    freqs = zip(vocab_1, np.array(count_mat_1.astype(bool).sum(axis=0)).flatten())  # toarray
    freqs = sorted(freqs, key=lambda x: -x[1])
    frequent_words_set = {w for w, f in freqs[:int(0.1*len(freqs))]}
    freqs = freqs[int(0.1*len(freqs)):] # ignore 10% most frequent tokens, we don't want to have too common tokens in the query list
    one_token_list = [w for w, c in random.sample(freqs, 1000)]
    one_token_idx_list = []
    for query in one_token_list:
        idx_doc = count_mat_1[:, np.where(vocab_1 == query)[0][0]]
        one_token_idx_list.append([p.name for p in path_list[idx_doc.nonzero()[0]]])

    # 300 2-token query
    # two_token_list, two_token_idx_list = [], []
    # while len(two_token_list) < 300:
    #     two_random_tokens = [w for w, c in random.sample(freqs, 2)] # manually adjust this number to calibrate the amount of retrieved paths
    #     idx_doc_1 = count_mat_1[:, np.where(vocab_1 == two_random_tokens[0])[0][0]]
    #     idx_doc_2 = count_mat_1[:, np.where(vocab_1 == two_random_tokens[1])[0][0]]
    #     intersection_idx = (np.array(idx_doc_1.todense()).flatten() *
    #                         np.array(idx_doc_2.todense()).flatten()).nonzero()[0]
    #     if len(intersection_idx):
    #         two_token_list.append(' '.join(two_random_tokens))
    #         two_token_idx_list.append([p.name for p in path_list[intersection_idx]])
    #         if len(two_token_list) % 10 == 0: print(len(two_token_list) / 300 * 100)
    two_token_list, two_token_idx_list = [], []
    while len(two_token_list) < 300:
        doc_id = random.choice(range(count_mat_1.shape[0])) # randomly select a document
        document_tokens = list(np.nonzero(count_mat_1[doc_id])[1])
        if len(document_tokens) < 3:
            continue
        two_tokens = random.sample(document_tokens, 2) # randomly select 2 tokens in the document
        if filter_frequent_2_and_3_token_queries:
            if any(vocab_1[t] in frequent_words_set for t in two_tokens):
                continue

        if ' '.join(vocab_1[two_tokens]) not in two_token_list:
            docs_with_token_1 = np.nonzero(count_mat_1[:, two_tokens[0]])[0] # search for all docs containing token 1
            docs_with_token_2 = np.nonzero(count_mat_1[:, two_tokens[1]])[0] # search for all docs containing token 2
            docs_with_2_tokens = set(docs_with_token_1).intersection(set(docs_with_token_2))
            two_token_idx_list.append([p.name for p in path_list[list(docs_with_2_tokens)]])
            two_token_list.append(' '.join(vocab_1[two_tokens]))

    # 200 3-token query
    # three_token_list, three_token_idx_list = [], []
    # while len(three_token_list) < 200:
    #     three_random_tokens = [w for w, c in random.sample(freqs, 3)] # manually adjust this number to calibrate the amount of retrieved paths
    #     idx_doc_1 = count_mat_1[:, np.where(vocab_1 == three_random_tokens[0])[0][0]]
    #     idx_doc_2 = count_mat_1[:, np.where(vocab_1 == three_random_tokens[1])[0][0]]
    #     idx_doc_3 = count_mat_1[:, np.where(vocab_1 == three_random_tokens[2])[0][0]]
    #     intersection_idx = (np.array(idx_doc_1.todense()).flatten() *
    #                         np.array(idx_doc_2.todense()).flatten() *
    #                         np.array(idx_doc_3.todense()).flatten()).nonzero()[0]
    #     if len(intersection_idx):
    #         three_token_list.append(' '.join(three_random_tokens))
    #         three_token_idx_list.append([p.name for p in path_list[intersection_idx]])
    #         if len(three_token_list) % 10 == 0: print(len(three_token_list) / 200 * 100)
    three_token_list, three_token_idx_list = [], []
    while len(three_token_list) < 200:
        doc_id = random.choice(range(count_mat_1.shape[0]))  # randomly select a document
        document_tokens = list(np.nonzero(count_mat_1[doc_id])[1])
        if len(document_tokens) < 4:
            continue
        three_tokens = random.sample(document_tokens, 3)  # randomly select 3 tokens in the document
        if filter_frequent_2_and_3_token_queries:
            if any(vocab_1[t] in frequent_words_set for t in three_tokens):
                continue

        if ' '.join(vocab_1[three_tokens]) not in three_token_list:
            docs_with_token_1 = np.nonzero(count_mat_1[:, three_tokens[0]])[0]  # search for all docs containing token 1
            docs_with_token_2 = np.nonzero(count_mat_1[:, three_tokens[1]])[0]  # search for all docs containing token 2
            docs_with_token_3 = np.nonzero(count_mat_1[:, three_tokens[2]])[0]  # search for all docs containing token 3
            docs_with_3_tokens = set.intersection(set(docs_with_token_1), set(docs_with_token_2), set(docs_with_token_3))
            three_token_idx_list.append([p.name for p in path_list[list(docs_with_3_tokens)]])
            three_token_list.append(' '.join(vocab_1[three_tokens]))

    # 300 2-gram query
    vectorizer_2 = joblib.load(f'{query_dir}/{persona_name}_vectorizer_2.pkl')
    count_mat_2 = vectorizer_2['count_mat']
    vocab_2 = vectorizer_2['vocab']
    freqs = zip(vocab_2, np.array(count_mat_2.astype(bool).sum(axis=0)).flatten())
    freqs = sorted(freqs, key=lambda x: -x[1])
    freqs = freqs[int(0.2*len(freqs)):] # ignore 20% most frequent tokens, we don't want to have too common tokens in the query list
    bigram_list, bigram_idx_list = [], []
    while len(bigram_list) < 300:
        bigram = random.choice(freqs)[0]
        if bigram not in two_token_list and bigram not in bigram_list:
            idx_doc_1 = count_mat_1[:, np.where(vocab_1 == bigram.split()[0])[0][0]]  # use count_mat_1 vocab_1
            idx_doc_2 = count_mat_1[:, np.where(vocab_1 == bigram.split()[1])[0][0]]  # use count_mat_1 vocab_1
            intersection_idx = (np.array(idx_doc_1.todense()).flatten() *
                                np.array(idx_doc_2.todense()).flatten()).nonzero()[0]
            if len(intersection_idx):
                bigram_list.append(bigram)
                bigram_idx_list.append([p.name for p in path_list[intersection_idx]])

    # 200 3-gram query
    vectorizer_3 = joblib.load(f'{query_dir}/{persona_name}_vectorizer_3.pkl')
    count_mat_3 = vectorizer_3['count_mat']
    vocab_3 = vectorizer_3['vocab']
    freqs = zip(vocab_3, np.array(count_mat_3.astype(bool).sum(axis=0)).flatten())
    freqs = sorted(freqs, key=lambda x: -x[1])
    freqs = freqs[int(0.3*len(freqs)):] # ignore 30% most frequent tokens, we don't want to have too common tokens in the query list
    trigram_list, trigram_idx_list = [], []
    while len(trigram_list) < 200:
        trigram = random.choice(freqs)[0]
        if trigram not in three_token_list and trigram not in trigram_list:
            idx_doc_1 = count_mat_1[:, np.where(vocab_1 == trigram.split()[0])[0][0]]  # use count_mat_1 vocab_1
            idx_doc_2 = count_mat_1[:, np.where(vocab_1 == trigram.split()[1])[0][0]]  # use count_mat_1 vocab_1
            idx_doc_3 = count_mat_1[:, np.where(vocab_1 == trigram.split()[2])[0][0]]  # use count_mat_1 vocab_1
            intersection_idx = (np.array(idx_doc_1.todense()).flatten() *
                                np.array(idx_doc_2.todense()).flatten() *
                                np.array(idx_doc_3.todense()).flatten()).nonzero()[0]
            if len(intersection_idx):
                trigram_list.append(trigram)
                trigram_idx_list.append([p.name for p in path_list[intersection_idx]])

    # sum all
    query_list = one_token_list + two_token_list + three_token_list + bigram_list + trigram_list
    idx_list = one_token_idx_list + two_token_idx_list + three_token_idx_list + bigram_idx_list + trigram_idx_list
    query_idx_map = [{query_list[i]: idx_list[i]} for i in range(len(query_list))]
    with open(save_path, 'w') as f:
        for pair in query_idx_map:
            f.write(json.dumps(pair) + '\n')


if __name__ == '__main__':
    random.seed(123)

    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--data_in", default="./data/persona_preprocess")
    ap.add_argument("--query_dir", default="./data/query")
    ap.add_argument("--filter_frequent_2_and_3_token_queries", action="store_true", default=False)
    args = ap.parse_args()

    for n_gram in range(1, 4): # 1 2 3
        construct_count_max(data_in=args.data_in, persona_name=args.persona, n_gram=n_gram,
                            save_path=f'{args.query_dir}/{args.persona}_vectorizer_{n_gram}.pkl')
    save_path = (
        f'{args.query_dir}/{args.persona}_ff23_query.json'
        if args.filter_frequent_2_and_3_token_queries
        else f'{args.query_dir}/{args.persona}_query.json'
    )
    select_query(data_in=args.data_in, persona_name=args.persona, query_dir=args.query_dir,
                 filter_frequent_2_and_3_token_queries=args.filter_frequent_2_and_3_token_queries,
                 save_path=save_path)
