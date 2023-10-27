import joblib
import random
from math import log
import numpy as np
from collections import Counter
from itertools import product

voc_size = 8000
posindex = []


def posindex_str():
    '''Make fake positional index out of 
    non-existent vocabulary and even less 
    existent documents'''
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



#posindex_str()

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
