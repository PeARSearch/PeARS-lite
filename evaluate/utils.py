import argparse
import pathlib
import random
import string
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, SnowballStemmer
import sys
from tqdm import tqdm
import numpy as np
from gensim.models import FastText
from sklearn.cluster import KMeans
from k_means_constrained import KMeansConstrained
import faiss


def clean_texts(text, language):
    """ Function to perform preprocessing """
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    lemmatizer = WordNetLemmatizer() if language == "english" else None
    stop_words = nltk.corpus.stopwords.words(language) if language in ["english", "french", "russian"] else []

    # Convert to lower cases
    text = text.lower()

    # Remove punctuations and numbers
    text = text.translate(translator)

    # Tokenization
    if language in ["english", "french", "russian"]:
        tokens = word_tokenize(text, language)
    else:
        tokens = text.split()

    # Lemmatization
    if language == "english":
        tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Remove stop words
    tokens = [token for token in tokens if token not in stop_words]

    # Join tokens
    clean_text = " ".join(tokens)

    # Return the output
    return clean_text


def preprocess_dataset(in_dir, out_dir, persona_name, language, remove_unk_filename_chars):
    # for root, dirs, file_name in os.walk(f'./persona/{persona_name}'):
    #     for dir in dirs:
    #         # print(os.path.join(root  + '_preprocess', dir))
    #         pathlib.Path(os.path.join(root, dir).replace('persona', 'persona_preprocess')).mkdir(parents=True, exist_ok=True)

    pathlib.Path(f'{out_dir}/{persona_name}').mkdir(parents=True, exist_ok=True)
    path_list = pathlib.Path(f'{in_dir}/{persona_name}/').glob('*.txt')
    for path in tqdm(path_list):
        text = clean_texts(str(path).split('/')[-1].replace('.txt', '').replace('_', ' ').replace('-', ' '), language) + ' '
        with open(path) as f:
            text += clean_texts(f.read(), language)
        if remove_unk_filename_chars:
            new_file_name = re.sub(r'[^a-zA-Z0-9-_.]', '', path.name)
        else:
            new_file_name = path.name
        with open(f'{out_dir}/{persona_name}/' + new_file_name, 'w') as f:
            f.write(text)


def create_proj_mat(seed=111, output_dim=128, input_dim=16000, proj_type='float', fruitfly_proj_size=5, extra_info=None):
    """
    Create a projection matrix to transform document representation.
    Args:
        seed (int, optional): Random seed.
        output_dim (int, optional): Output dimension.
        input_dim (int, optional): Input dimension.
        proj_type (str, optional): The type of projection method to use. Options:
            - 'float': Random float values between 0 and 1.
            - 'ach': Achlioptas's method, using -1, 0, and 1 values with proportion and scaling.
            - 'fruitfly': Binary 0 and 1, with full vocab coverage.
        fruitfly_proj_size (int, optional): The number of 1 connection for each output neuron in 'fruitfly' method.
        extra_info (Any, optional): for future extensions.
    Returns:
        numpy.ndarray or None: The generated projection matrix or None.
    """

    rng = np.random.default_rng(seed)
    if proj_type == 'float':
        proj_mat = rng.random(size=(output_dim, input_dim))

    elif proj_type == 'ach': # Achlioptas's method
        scale = output_dim
        proportion = [1 / (2 * scale), 1 - 1 / scale, 1 / (2 * scale)]
        proj_mat = rng.choice([-1, 0, 1], size=(output_dim, input_dim), p=proportion)
        proj_mat = proj_mat * np.sqrt(scale / output_dim)

    elif proj_type == 'fruitfly':
        proj_mat = np.zeros((output_dim, input_dim))
        idx = list(range(input_dim))
        rng.shuffle(idx)
        used_idx = idx.copy()
        c = 0
        while c < output_dim:
            for i in range(0, len(idx), fruitfly_proj_size):
                p = idx[i:i + fruitfly_proj_size]
                for j in p:
                    proj_mat[c][j] = 1
                c += 1
                if c >= output_dim:
                    break
            rng.shuffle(idx)  # reshuffle if needed -- if all output neurons are not filled
            used_idx.extend(idx)
    else:
        proj_mat = None
    return proj_mat.T  # transpose to vocab_shape x output_shape


def group_tokens():
    """
    Create projection matrices by grouping similar tokens together. Semantic vectors for tokens
    are extracted from a pretrained distributional semantic model, e.g. in this case FastText.
    """

    vocab = []
    with open('../app/api/models/en/enwiki.vocab') as f:
        for line in f:
            vocab.append(line.split()[0])
    vocab = np.array(vocab)

    # # read fasttext model and extract the word vectors for every words in the vocab
    # model = FastText.load("../../datasets/projection_experiments/dist_vec/en.fasttext")
    # tok_vec = []
    # for v in vocab:
    #     tok_vec.append(model.wv.get_vector(v))
    # np.save("../../datasets/projection_experiments/dist_vec/en_tok_vec", np.array(tok_vec))

    tok_vec = np.load("../../datasets/projection_experiments/dist_vec/en_tok_vec.npy").astype(float)
    for seed in range(111, 666, 111):
        # kmeans = KMeans(n_clusters=256, random_state=seed, n_init="auto").fit(tok_vec)  # kmean scikit learn
        # kmeans from facebook faiss lib, which has more balanced number of members per class
        kmeans = faiss.Kmeans(d=tok_vec.shape[1], k=256, seed=seed,
                              min_points_per_centroid=10, max_points_per_centroid=63, # min max points does not work
                              niter=200, verbose=True)
        kmeans.train(tok_vec)
        labels = kmeans.index.search(tok_vec, 1)[1].flatten()
        # # print the clusters with their members
        # labels = kmeans.labels_
        # group = dict()
        # for label in set(labels):
        #     group[label] = list(vocab[np.where(labels == label)])

        # crate a projection matrix
        proj_mat = np.zeros((256, 16000))
        for label in set(labels):
            proj_mat[label][np.where(labels == label)] = 1
        np.save(f"../../datasets/projection_experiments/proj_mat/256/fasttext_min10/{seed}", proj_mat.T)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--data_in", default="./data/persona")
    ap.add_argument("--data_out", default="./data/persona_preprocess")
    ap.add_argument("--language", default="english")
    ap.add_argument("--remove_unk_filename_chars", type=int, default=1)
    args = ap.parse_args()

    preprocess_dataset(in_dir=args.data_in, out_dir=args.data_out, persona_name=args.persona, language=args.language, remove_unk_filename_chars=args.remove_unk_filename_chars)

    # for seed in range(111, 666, 111):
    #     proj_mat = create_proj_mat(seed=seed, output_dim=256, proj_type='fruitfly', fruitfly_proj_size=63)
    #     np.save(f'../../datasets/projection_experiments/proj_mat/256/fruitfly_63/{seed}.npy', proj_mat)

    # group_tokens()
