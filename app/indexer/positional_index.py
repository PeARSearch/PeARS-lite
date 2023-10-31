import argparse
import joblib
import json
from tqdm import tqdm
import random
import glob
from math import log
import numpy as np
from collections import Counter, OrderedDict
from itertools import product
import time

from app.indexer.vectorizer import read_vocab
from app.indexer.mk_page_vector import add_eofs
from app.api.models import sp


_POSINDEX_CACHE = {}


def _map_docs_to_index(documents):
    doc_to_index = {}
    index_to_doc = {}
    doc_id = 0
    for doc in documents:
        doc_to_index[doc] = doc_id
        index_to_doc[doc_id] = doc
        doc_id += 1
    return doc_to_index, index_to_doc

def index_documents(vocab, spm_model_path, documents, out_path, add_end_of_word_markers):
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
            if add_end_of_word_markers:
                doc_tokens = add_eofs(tokens=doc_tokens).split()
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


def _pair_score(prev_pos, current_pos):
    pair_scores = []
    pairs = list(product(prev_pos, current_pos))
    for pair in pairs:
        dist = abs(pair[1]-pair[0])
        if dist == 0:
            continue
        dist_score = max(1-log(dist,10), 0)
        pair_scores.append(dist_score) #the score is 1 for a distance of 1, and 0 for a distance of 10 or greater
    return pair_scores


def score(posl, enforce_subwords=True):
    '''Just one way out of a million to compute
    a score based on the distance between query tokens.'''
    print("\nPOSITIONS IN DOC",posl)
    
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
                print("\nPAIR SCORES",scores)
                if pair_scores:
                    scores.extend(pair_scores)
                else:
                    scores.append(1.0)
            prev_pos = current_pos

    if enforce_subwords:
        return np.mean(scores)  # meaning: the fraction of words that were completely matched (= all subwords consecutive)
    else:
        return np.max(scores)  # meaning: 1.0 if there is at least one pair of tokens that is consecutive both in the query and in the document. Otherwise a fraction of this. 

def _search(query, posindex, doc_to_index, index_to_doc, vocab, inverted_vocab, add_posttok_eof, scoring_method="all_subwords"):
    
    assert scoring_method in ["all_subwords", "token_distance"]
    if scoring_method == "all_subwords":
        enforce_subwords = True
    else:
        enforce_subwords = False

    query_tokens = [wp for wp in sp.encode_as_pieces(query)]
    if add_posttok_eof:
        query_tokens = add_eofs(tokens=query_tokens).split()

    query_vocab_ids = [vocab.get(wp) for wp in query_tokens]
    if any([i is None for i in query_vocab_ids]):
        print("WARNING: there were unknown tokens")
        print(query_tokens, query_vocab_ids)
        query_vocab_ids = [i for i in query_vocab_ids if i is not None]

    print(f"QUERY: {repr(query)}\n-> {query_tokens} ({query_vocab_ids})")

    idx = []
    for w in query_vocab_ids:
        idx.append(set(posindex[w].keys()))        # get docs containing token

    matching_docs = list(set.intersection(*idx))   # intersect doc lists to only retain the docs that contain *all* tokens
    doc_scores = {}
    for doc in matching_docs:
        print("=======================")
        filename = index_to_doc[doc]
        print(f"DOC {doc} => {filename}")
        positions = []
        for w in query_vocab_ids:
            token_str = inverted_vocab[w]
            token_positions = posindex[w][doc]
            if token_str.startswith("▁"):
                positions.append((token_positions,))
            else:
                positions[-1] += (token_positions,)
            print("DOC",doc,"Q WORD", token_str, token_positions)

        print(positions)
        final_score = score(positions, enforce_subwords=enforce_subwords)
        doc_scores[filename] = final_score
        print("\nFINAL SCORE FOR DOC", doc, final_score)
        print("=======================\n\n")
    return doc_scores


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


def index_and_test(spm_model_path=None, document_dir=None, output_name="tester", add_end_of_word_markers=False):
    """
    Create an inverted index from a document directory and run a basic test
    """

    if spm_model_path is None:
        vocab_file = "app/api/models/en/enwiki.vocab"
        spm_model_path = "app/api/models/en/enwiki.model"
    else:
        vocab_file = spm_model_path[:-6] + ".vocab"

    vocab, inverted_vocab, _ = read_vocab(vocab_file)
    if add_end_of_word_markers:
        vocab = OrderedDict(vocab) # make sure we can rely on the order
        vocab.update({f"{w}▁": v + len(vocab) for w, v in vocab.items()})
        inverted_vocab = {v: w for w, v in vocab.items()}

    if document_dir is None:
        document_dir = "app/static/testdocs/tester/localhost.localdomain/Downloads"

    documents = glob.glob(f"{document_dir}/**/*.txt", recursive=True)
    
    out_path = f"app/static/posindex/{output_name}{'.eow' if add_end_of_word_markers else ''}.str"
    posindex, doc_to_index, index_to_doc = index_documents(vocab, spm_model_path, documents, out_path, add_end_of_word_markers)

    time_0 = time.time()

    sp.load(spm_model_path)
    
    time_1 = time.time()

    query_text = "roses grandma"
    _search(query_text, posindex, doc_to_index, index_to_doc, vocab, inverted_vocab, add_end_of_word_markers)
    
    time_2 = time.time()
    print(f"Time for loading tokenizer: {time_1 - time_0}")
    print(f"Search time: {time_2 - time_1}")


def run_posindex_search(query, inverted_index_path, vocab, reverse_vocab, add_end_of_word_markers, scoring_method="all_subwords"):
    global _POSINDEX_CACHE

    if inverted_index_path in _POSINDEX_CACHE:
        posindex = _POSINDEX_CACHE[inverted_index_path]["posindex"]
        doc_to_index = _POSINDEX_CACHE[inverted_index_path]["doc_to_index"]
        index_to_doc = _POSINDEX_CACHE[inverted_index_path]["index_to_doc"]
    else:
        posindex = joblib.load(inverted_index_path)
        with open(inverted_index_path.replace(".str", ".doc_to_index.json"), encoding="utf-8") as f:
            doc_to_index = json.load(f)
        with open(inverted_index_path.replace(".str", ".index_to_doc.json"), encoding="utf-8") as f:
            index_to_doc = {int(k): v for k, v in json.load(f).items()}  # json keys are always strings -> convert back to ints
        
        _POSINDEX_CACHE[inverted_index_path] = {
            "posindex": posindex,
            "doc_to_index": doc_to_index,
            "index_to_doc": index_to_doc
        }

    return _search(query, posindex, doc_to_index, index_to_doc, vocab, reverse_vocab, add_end_of_word_markers, scoring_method)
    

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    # spm_model_path=None, document_dir=None, output_name="tester", add_posttok_eof=False
    ap.add_argument("--spm_model_path", default=None)
    ap.add_argument("--document_dir", default=None)
    ap.add_argument("--output_name", default=None)
    ap.add_argument("--add_end_of_word_markers", action="store_true", default=False)
    args = ap.parse_args()

    index_and_test(args.spm_model_path, args.document_dir, args.output_name, args.add_end_of_word_markers)