import os
import argparse
import pathlib
import glob
import random
import string
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, SnowballStemmer
import sys
from tqdm import tqdm
import pandas as pd


def clean_texts(text, language):
    """ Function to perform preprocessing """
    punctuation = string.punctuation + "’" # add missing apostrophe 

    translator = str.maketrans(punctuation, ' ' * len(punctuation))
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
    path_list = glob.glob(f'{in_dir}/{persona_name}/**/*.txt', recursive=True)
    for path in tqdm(path_list):
        text = clean_texts(path.split('/')[-1].replace('.txt', '').replace('_', ' ').replace('-', ' '), language) + ' '
        with open(path) as f:
            text += clean_texts(f.read(), language)
        if remove_unk_filename_chars:
            new_file_name = re.sub(r'[^a-zA-Z0-9-_.]', '', os.path.basename(path))
        else:
            new_file_name = os.path.basename(path)
        with open(f'{out_dir}/{persona_name}/' + new_file_name, 'w') as f:
            f.write(text)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("persona")
    ap.add_argument("--data_in", default="./data/persona")
    ap.add_argument("--data_out", default="./data/persona_preprocess")
    ap.add_argument("--language", default="english")
    ap.add_argument("--remove_unk_filename_chars", type=int, default=1)
    args = ap.parse_args()

    preprocess_dataset(in_dir=args.data_in, out_dir=args.data_out, persona_name=args.persona, language=args.language, remove_unk_filename_chars=args.remove_unk_filename_chars)





