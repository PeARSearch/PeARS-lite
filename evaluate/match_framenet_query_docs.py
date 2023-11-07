import os
import nltk
from collections import defaultdict
import json
import math
import glob

from tqdm import tqdm

from utils import clean_texts
from create_query_framenet import get_frame_structures


def _get_raw_doc_name(preproc_doc_name, persona, persona_):
    # todo: make sure datasets have the same names between the raw & preprocessed corpora
    raw_doc = preproc_doc_name.replace(f"/personas_preprocessed/{persona_}/", f"/personas_raw/{persona}/")
    if not os.path.exists(raw_doc):
        raw_dir = os.path.split(raw_doc)[0]
        for f in glob.glob(f"{raw_dir}/**/*", recursive=True):
            if os.path.basename(f) == os.path.basename(raw_doc):
                return f
        return None
    return raw_doc


def main():

    # query_files = glob.glob("../../../datasets/personas/personas_fn_queries/*_query.json")
    query_files = [
        ("/home/gosse/Documents/PossibleWorlds/NGI-search/datasets/personas/personas_fn_queries/news-dataset_query.json", 9)
    ]

    for qf, chunk in query_files:
        
        if chunk is None: # process entire file
            q2g_file = qf.replace("_query.json", "_q2g.json")
            q2g_plus_file = qf.replace("_query.json", "_q2g_plus.json")
        else:
            q2g_file = qf.replace("_query.json", f"_q2g.c{chunk:02}.json")
            q2g_plus_file = qf.replace("_query.json", f"_q2g_plus.c{chunk:02}.json")

        if os.path.exists(q2g_plus_file):
            continue

        persona = os.path.basename(qf).replace("_query.json", "")
        if persona == "news-dataset":
            persona_ = "2_news"
        else:
            persona_ = persona
        print(persona)
        language = "french" if "_fr_" in persona else "russian" if "_ru_" in persona else "english"
        print(language)
        fulltext_files = glob.glob(f"../../../datasets/personas/personas_preprocessed/{persona_}/**/*.txt", recursive=True)

        if chunk is not None:
            num_docs = len(fulltext_files)
            chunk_size = math.ceil(num_docs / 10)
            first_doc = chunk_size * chunk
            last_doc = first_doc + chunk_size
            fulltext_files = fulltext_files[first_doc:last_doc]
            print(f"Processing documents {first_doc}:{last_doc}")              

        
        with open(qf, encoding="utf-8") as f:
            queries = json.load(f)
            print(len(queries))

        document_matches = {qry["query"]: [qry["_txt_meta"]["document"]] for qry in queries}
        sentence_matches = {
            qry["query"]: [
                {
                    "doc": _get_raw_doc_name(qry["_txt_meta"]["document"], persona, persona_), 
                    "sent": qry["_txt_meta"]["sentence"]
                }        
            ] 
            for qry in queries
        }
        frame_matches = {
            qry["query"]: [
                {
                    "doc": _get_raw_doc_name(qry["_txt_meta"]["document"], persona, persona_), 
                    "sent": qry["_txt_meta"]["sentence"],
                    "frame": qry["_fn_meta"]["frame"],
                    "frame_structure": qry["_fn_meta"]["frame_structure"]
                }        
            ] 
            for qry in queries
        }

        print(len(document_matches))

        for doc in tqdm(fulltext_files):
            raw_doc = _get_raw_doc_name(doc, persona, persona_)

            with open(doc, encoding="utf-8") as f:
                doc_text = f.read()  # the texts are already preprocessed, but do it again to remove the weird apostrophe
            doc_words = {w for w in doc_text.split()}
            doc_sentences = None  # placeholder -- only do sentence tokenization in case of at least one match
            doc_frames = {}

            for qry in queries:
                if qry["_category"] == "place_relations":
                    continue  # weird category, ignore it


                query_words = set(qry["query"].split())

                # check if all words occur in the documents --> document match 
                if all([w in doc_words for w in query_words]):
                    if doc != qry["_txt_meta"]["document"]:
                        tqdm.write(f"QUERY {qry['query']}")
                        tqdm.write(f"\tDOC MATCH {doc}")
                        document_matches[qry["query"]].append(raw_doc)

                    # if we have a document match, check if there is (at least one) sentence in 
                    # the document in which all of the words occur --> sentence match(es)
                    if doc_sentences is None:
                        with open(raw_doc, encoding="utf-8") as f:
                            raw_doc_text = f.read()
                        doc_sentences = [(raw_s, clean_texts(raw_s, language)) for raw_s in nltk.sent_tokenize(raw_doc_text, language)]
                    
                    for raw_s, cleaned_s in doc_sentences:
                        if raw_s == qry["_txt_meta"]["sentence"]:
                            continue

                        if all([w in cleaned_s.split() for w in query_words]):
                            sentence_matches[qry["query"]].append({
                                "doc": raw_doc,
                                "sentence": raw_s
                            })
                            tqdm.write(f"\t\tSENT MATCH {raw_s}")

                            # if we have a sentence match: check if there is a frame structure 
                            # in the sentence that all of the query words occur in
                            # (indicating that they are somehow semantically connected)
                            if raw_s not in doc_frames:
                                doc_frames[raw_s] = get_frame_structures(raw_s)
                            for fs_id, fs in doc_frames[raw_s].items():
                                fs_words = set()
                                for role, span in fs.items():
                                    for span_w in clean_texts(span, language).split():
                                        fs_words.add(span_w)
                                if all([w in fs_words for w in query_words]):
                                    frame_matches[qry["query"]].append({
                                        "doc": raw_doc,
                                        "sentence": raw_s,
                                        "frame": fs_id.split(".")[1],
                                        "frame_structure": fs
                                    })
                                    tqdm.write(f"\t\t\tFRAME MATCH {fs_id}")


        with open(q2g_file, "w", encoding="utf-8") as f:
            for qry, docs in document_matches.items():
                f.write(json.dumps({qry: docs}, ensure_ascii=False, sort_keys=True) + os.linesep)

        with open(q2g_plus_file, "w", encoding="utf-8") as f:
            for qry, docs in document_matches.items():
                entry = {
                    qry: {
                        "document_matches": docs,
                        "sentence_matches": sentence_matches[qry],
                        "frame_matches": frame_matches[qry]
                    }
                }
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + os.linesep)



def merge_partial_files(plus_files, plus_out_name):

    base_files = [f.replace("_q2g_plus.", "_q2g.") for f in plus_files]
    base_out_name = plus_out_name.replace("_q2g_plus.json", "_q2g.json")

    plus_fs = [open(f, encoding="utf-8") for f in plus_files]
    base_fs = [open(f, encoding="utf-8") for f in base_files]

    with open(plus_out_name, "w", encoding="utf-8") as pfo, open(base_out_name, "w", encoding="utf-8") as bfo:
        base_lines_gen = zip(*base_fs)
        for plus_lines in zip(*plus_fs):
            base_lines = next(base_lines_gen)
            plus_out = {}
            base_out = {}
            doc_names = set()
            query_words = ""

            # plus file lines
            for i, ql in enumerate(plus_lines):
                line_data = json.loads(ql)
                query_words = list(line_data.keys())[0]
                
                # initialize dictionary from the first file's entry
                if i == 0:
                    plus_out[query_words] = list(line_data.values())[0]
                    doc_names.update(list(line_data.values())[0]["document_matches"])
                # subsequent files:
                else:
                    for match_key, match_list in list(line_data.values())[0].items():
                        if match_key == "document_matches":
                            for doc in match_list:
                                if doc not in doc_names:
                                    plus_out[query_words][match_key].append(doc)
                        else:
                            for match in match_list:
                                if match["doc"] not in doc_names:
                                    plus_out[query_words][match_key].append(match)

            pfo.write(json.dumps(plus_out) + os.linesep)

            # base file lines
            for i, ql in enumerate(base_lines):
                line_data = json.loads(ql)

                # initialize dictionary from the first file's entry
                if i == 0:
                    base_out[query_words] = list(line_data.values())[0]
                    doc_names.update(list(line_data.values())[0])
                # subsequent files:
                else:
                    for doc in list(line_data.values())[0]:
                        if doc not in doc_names:
                            base_out[query_words].append(doc)
            bfo.write(json.dumps(base_out) + os.linesep)



if __name__ == "__main__":
    # main()
    merge_partial_files(sorted(glob.glob("/home/gosse/Documents/PossibleWorlds/NGI-search/datasets/personas/personas_fn_queries/news-dataset_q2g_plus.c*.json")), "/home/gosse/Documents/PossibleWorlds/NGI-search/datasets/personas/personas_fn_queries/news-dataset_q2g_plus.json")
