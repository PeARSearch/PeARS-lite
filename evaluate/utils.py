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
    return proj_mat.T


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
    #     proj_mat = create_proj_mat(seed=seed, output_dim=128, proj_type='ach')
    #     np.save(f'../../datasets/projection_experiments/proj_mat/128/ach/{seed}.npy', proj_mat)

