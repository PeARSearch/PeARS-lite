import pathlib
import random
import string
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import sys
from tqdm import tqdm
import pandas as pd


def clean_texts(text):
    """ Function to perform preprocessing """
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    lemmatizer = WordNetLemmatizer()
    stop_words = nltk.corpus.stopwords.words('english')

    # Convert to lower cases
    text = text.lower()

    # Remove punctuations and numbers
    text = text.translate(translator)

    # Tokenization
    tokens = word_tokenize(text)
    # tokens = text.split()

    # Lemmatization
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Remove stop words
    tokens = [token for token in tokens if token not in stop_words]

    # Join tokens
    clean_text = " ".join(tokens)

    # Return the output
    return clean_text


def preprocess_dataset(persona_name):
    # for root, dirs, file_name in os.walk(f'./persona/{persona_name}'):
    #     for dir in dirs:
    #         # print(os.path.join(root  + '_preprocess', dir))
    #         pathlib.Path(os.path.join(root, dir).replace('persona', 'persona_preprocess')).mkdir(parents=True, exist_ok=True)

    pathlib.Path(f'./data/persona_preprocess/{persona_name}').mkdir(parents=True, exist_ok=True)
    path_list = pathlib.Path(f'./data/persona/{persona_name}/').glob('*.txt')
    # print(path_list)
    for path in tqdm(path_list):
        text = clean_texts(str(path).split('/')[-1].replace('.txt', '').replace('_', ' ').replace('-', ' ')) + ' '
        with open(path) as f:
            text += clean_texts(f.read())
        new_file_name = re.sub(r'[^a-zA-Z0-9-_.]', '', path.name)
        with open(f'./data/persona_preprocess/{persona_name}/' + new_file_name, 'w') as f:
            f.write(text)


if __name__ == '__main__':
    preprocess_dataset(persona_name=sys.argv[1])





