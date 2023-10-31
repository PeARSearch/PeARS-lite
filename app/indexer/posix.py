import joblib
from os.path import join, dirname, realpath
from app import vocab

def load_posix():
    dir_path = dirname(dirname(realpath(__file__)))
    posix_path = join(dir_path,'static','posix')
    posix = joblib.load(join(posix_path,'posix.txt'))
    return posix

def dump_posix(posindex):
    dir_path = dirname(dirname(realpath(__file__)))
    posix_path = join(dir_path,'static','posix')
    joblib.dump(posindex, join(posix_path,'posix.txt'))


def posix_doc(text, doc_id):
    posindex = load_posix()
    print(text)
    print(text.split())
    for pos, token in enumerate(text.split()):
        if token not in vocab:
            # tqdm.write(f"WARNING: token \"{token}\" not found in vocab")
            continue
        token_id = vocab[token]
        if doc_id in posindex[token_id]:
            posindex[token_id][doc_id] += f"|{pos}"
        else:
            posindex[token_id][doc_id] = f"{pos}"
    dump_posix(posindex)
