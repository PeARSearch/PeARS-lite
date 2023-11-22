import glob
import json

from tqdm import tqdm

from gensim.models import FastText
from gensim.models.callbacks import CallbackAny2Vec
import nltk
import sentencepiece as spm


# copied from https://radimrehurek.com/gensim/models/callbacks.html
class EpochLogger(CallbackAny2Vec):
    def __init__(self):
        self.epoch = 0

    def on_epoch_begin(self, model):
        print("Epoch #{} start".format(self.epoch))

    def on_epoch_end(self, model):
        print("Epoch #{} end".format(self.epoch))
        self.epoch += 1


def generate_training_corpus(corpus_files, nltk_lang, sp, lim=None):
    total_sentences = 0
    total_words = 0
    for cf in corpus_files:
        with open(cf, encoding="utf-8") as f:
            for line in tqdm(f):
                if lim and total_words > lim:
                    return

                sentences = nltk.sent_tokenize(line, language=nltk_lang)
                for sent in sentences:
                    total_sentences += 1
                    total_words += len(sent.split())
                    if total_sentences % 100_000 == 0:
                        tqdm.write(f"S={total_sentences} | W={total_words}")
                    yield [wp for wp in sp.encode_as_pieces(sent.lower())]

# train fasttext on wikidump data
def train_fasttext(lang, corpus_files):
    nltk_lang = (
        "english" if lang == "en" else 
        "french" if lang == "fr" else 
        "russian" if lang == "ru" else 
        "english"
    )

    spm_model_path = f"app/api/models/{lang}/{lang}wiki.model"
    sp = spm.SentencePieceProcessor()
    sp.load(spm_model_path)

    max_words = 45_000_000  # Slovenian has 49_177_418 lines of raw text, round down to 2.5M and use as limit for all languages 
    # max_words = 1_000_000
    training_corpus = list(generate_training_corpus(corpus_files, nltk_lang, sp, lim=max_words))

    model = FastText(vector_size=100, window=5, min_count=5)
    print("Building vocab...")
    model.build_vocab(corpus_iterable=training_corpus)
    
    print("Training model...")
    model.train(corpus_iterable=training_corpus, total_examples=model.corpus_count, epochs=10, callbacks=[EpochLogger()])
    model.save(f"evaluate/fasttext_models/{lang}.fasttext")
    print("Training completed!")


def expand_query(qry, sp, ftm, max_expansions=5):
    qry_tokens = [wp for wp in sp.encode_as_pieces(qry.lower())]
    print("TOKENS", qry_tokens)
    
    expansions = []
    cur_expansion = [(wp, 1.0) for wp in qry_tokens]
    cur_sim_tokens = [ftm.wv.most_similar(wp) for wp in qry_tokens]
    cur_index = 0
    sim_depth = 0

    def _is_single_token_word(w_idx):
        if w_idx == len(qry_tokens) - 1:
            return True
        elif qry_tokens[w_idx + 1][0].startswith("▁"):
            return True
        return False

    def _save_expansion():
        # save the previously built expansion
        expansion_str = "".join([wp for wp, ss in cur_expansion if wp]).replace("▁", " ").strip()
        if expansion_str not in expansions:  # avoid duplicates
            expansions.append(expansion_str)
            str_with_probs = (
                "".join([f"{wp}:{ss:.2f}" for wp, ss in cur_expansion if wp])
                .replace("▁", " ")
                .replace(":1.00", "")
                .strip()
            )
            print("\tEXP", str_with_probs)

        # reset the expansion to the original query
        for i, _ in enumerate(cur_expansion):
            cur_expansion[i] = (qry_tokens[i], 1.0)


    while len(expansions) < max_expansions:

        cur_tok = cur_expansion[cur_index][0]
        if cur_tok.startswith("▁") and _is_single_token_word(cur_index):
            _save_expansion()

            # get next-most similar token for current position
            sim_tok, sim_score = cur_sim_tokens[cur_index][sim_depth]
            if sim_score > 0.7:
                cur_expansion[cur_index] = (sim_tok, sim_score)

        # go to next token
        cur_index = (cur_index + 1) % len(qry_tokens)
    
        # skip empty words
        if cur_index == 0 and len(expansions) == 0:
            expansions.append(qry)
            break
        elif cur_index == 0:
            sim_depth += 1
            _save_expansion()
            if sim_depth == len(cur_sim_tokens[cur_index]):
                break

    return expansions

def test_query_expansion():
    queries = []
    with open("../../datasets/personas/personas_fn_queries/2_news_q2g.json") as f:
        for line in f:
            line_data = json.loads(line)
            query = list(line_data.keys())[0]
            queries.append(query)

    # queries = [
    #     "new westernish flick josh"
    # ]

    sp = spm.SentencePieceProcessor()
    sp.load("app/api/models/en/enwiki.model")
    fasttext_model = FastText.load("evaluate/fasttext_models/en.fasttext")

    for qry in queries:
        print("QUERY", qry)
        _ = expand_query(qry, sp, fasttext_model)
        print("\n\n")


if __name__ == "__main__":
    # train_fasttext("sl", sorted(glob.glob("../wikiloader/data/sl/*.raw.txt")))
    # train_fasttext("en", sorted(glob.glob("../wikiloader/data/en/*.raw.txt")))
    # train_fasttext("fr", sorted(glob.glob("../wikiloader/data/fr/*.raw.txt")))
    # train_fasttext("ru", sorted(glob.glob("../wikiloader/data/ru/*.raw.txt")))
    test_query_expansion()