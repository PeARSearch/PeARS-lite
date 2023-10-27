import joblib
import json
from tqdm import tqdm
import random
import glob
from math import log
import numpy as np
from collections import Counter
from itertools import product

from app.indexer.vectorizer import read_vocab
from app.api.models import sp


def _map_docs_to_index(documents):
    doc_to_index = {}
    index_to_doc = {}
    doc_id = 0
    for doc in documents:
        doc_to_index[doc] = doc_id
        index_to_doc[doc_id] = doc
        doc_id += 1
    return doc_to_index, index_to_doc

def index_documents(vocab, spm_model_path, documents, out_path):
    """
    Make a positional index out of slightly more existent vocabulary and documents
    """
    
    doc_to_index, index_to_doc = _map_docs_to_index(documents)
    with open(out_path.replace(".str", ".doc_to_index.json"), "w", encoding="utf-8") as f:
        json.dump(doc_to_index, f)
    with open(out_path.replace(".str", ".index_to_doc.json"), "w", encoding="utf-8") as f:
        json.dump(index_to_doc, f)

    posindex = [{} for _ in range(len(vocab))]

    sp.load(spm_model_path)
    for doc in tqdm(documents):
        with open(doc, encoding="utf-8") as f:
            doc_text = f.read().strip()
            doc_tokens = [wp for wp in sp.encode_as_pieces(doc_text.lower())]
            for pos, token in enumerate(doc_tokens):
                if token not in vocab:
                    # tqdm.write(f"WARNING: token \"{token}\" not found in vocab")
                    continue
                token_id = vocab[token]
                doc_id = doc_to_index[doc]
                if doc_id in posindex[token_id]:
                    posindex[token_id][doc_id] += f"|{pos}"
                else:
                    posindex[token_id][doc_id] = f"{pos}"

    joblib.dump(posindex, out_path)
    with open(out_path.replace(".str", ".json"), "w", encoding="utf-8") as f:
        json.dump(posindex, f)
    
    return posindex, doc_to_index, index_to_doc 


def generate_artificial_index():
    '''Make fake positional index out of 
    non-existent vocabulary and even less 
    existent documents'''
    voc_size = 8000
    posindex = []

    ndocs = 100                           # num docs
    freqs = np.random.zipf(1.8, voc_size) # make a Zipfian distribution
    n = np.sum(freqs)                     # corpus size
    for i in range(voc_size):             # one index entry per vocab item
        posindex.append({})               # create empty dict
        f = freqs[i]                      # the freq of this item according to the Zipfian distribution
        print('#',i, 'FREQ',f)
        docs = list(range(ndocs))
        counts = Counter()
        for _ in range(f):
            counts[random.choice(docs)] += 1    # randomly allocate the occurrences of this lexical item to documents
        for doc in docs:                        # for each doc
            m = ""
            pos = list(range(int(n / ndocs)))   # positions in document (each doc has equal length, equal to corpus size / num docs)
            random.shuffle(pos)                 # shuffle positions 
            pos =  pos[:counts[doc]]            # get as many positions as we have occurrences of the lexical item. 
                                                # NB: buggy, two vocab items can be allocated to the same position, but doesn't matter for our purposes here.
            pos = sorted(pos)                   # sort those positions in order
            for p in pos:
                m+=str(p)+'|'                   # write positions to a string
            if m != "":
                posindex[i][doc] = m[:-1]       # add positions to the document ID slot for that vocab item
        #print(posindex[i])
    joblib.dump(posindex,'posindex.str')        # dump the index to check size

def score(posl):
    '''Just one way out of a million to compute
    a score based on the distance between query tokens.'''
    print("\nPOSITIONS IN DOC",posl)
    scores = []
    prev_pos = [int(i) for i in posl[0].split('|')]
    for p in posl[1:]:
        current_pos = [int(i) for i in p.split('|')]
        pairs = list(product(prev_pos, current_pos))
        for pair in pairs:
            dist = abs(pair[1]-pair[0])
            #print("DIST",dist)
            #print("SCORE",1-log(dist,10))
            scores.append(max(1-log(dist,10), 0)) #the score is 1 for a distance of 1, and 0 for a distance of 10 or greater
        prev_pos = current_pos
    print("\nSCORES",scores)
    return np.max(scores)


def test_artificial():
    generate_artificial_index()

    posindex = joblib.load('posindex.str')

    query = [1118, 7699] # Sample query
    print("\nQUERY",query)

    idx = []
    for w in query:
        idx.append(set(posindex[w].keys()))        # get docs containing token

    matching_docs = list(set.intersection(*idx))   # intersect doc lists to only retain the docs that contain *all* tokens

    for doc in matching_docs:
        positions = []
        for w in query:
            #print("DOC",doc,"Q WORD",w, posindex[w][doc])
            positions.append(posindex[w][doc])
        #print(positions)
        print("\nFINAL SCORE FOR DOC",doc,score(positions))


def test_real():

    vocab_file = "app/api/models/en/enwiki.vocab"
    spm_model_path = "app/api/models/en/enwiki.model"

    vocab, inverted_vocab, _ = read_vocab(vocab_file)
    tester_documents = glob.glob("app/static/testdocs/tester/localhost.localdomain/Downloads/*.txt")
    
    out_path = "app/static/posindex/tester.str"
    posindex, doc_to_index, index_to_doc = index_documents(vocab, spm_model_path, tester_documents, out_path)

    sp.load(spm_model_path)
    query_text = "man hospitalized"
    query_tokens = [wp for wp in sp.encode_as_pieces(query_text)]
    query_vocab_ids = [vocab[wp] for wp in query_tokens]
    print(f"QUERY: {repr(query_text)}\n-> {query_tokens} ({query_vocab_ids})")

    idx = []
    for w in query_vocab_ids:
        idx.append(set(posindex[w].keys()))        # get docs containing token

    matching_docs = list(set.intersection(*idx))   # intersect doc lists to only retain the docs that contain *all* tokens
    for doc in matching_docs:
        print("=======================")
        positions = []
        for w in query_vocab_ids:
            print("DOC",doc,"Q WORD", inverted_vocab[w], posindex[w][doc])
            positions.append(posindex[w][doc])
        print(positions)
        print("\nFINAL SCORE FOR DOC", doc, score(positions))
        print("=======================\n\n")
 

if __name__ == "__main__":
    test_real()