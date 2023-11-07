import os
import argparse
import json
import numpy as np
import sys
from collections import defaultdict


def _read_query_and_res_files(query_file, res_file, doc_pos_mode):
    true_path_list = []
    with open(query_file) as f:
        for line in f:
            if not doc_pos_mode:
                docs = list(json.loads(line).values())[0]
                docs = list({os.path.basename(d) for d in docs})
                true_path_list.append(docs)
            else:
                query_data = list(json.loads(line).values())[0]
                if doc_pos_mode == "document":
                    docs = query_data["document_matches"]
                elif doc_pos_mode == "sentence":
                    docs = [sm["doc"] for sm in query_data["sentence_matches"]]
                else:
                    docs = [fm["doc"] for fm in query_data["frame_matches"]]
                true_path_list.append(list({os.path.basename(d) for d in docs}))

    res_path_list = []
    with open(res_file) as f:
        for line in f:
            res_path_list.append(list(json.loads(line).values())[0])

    return true_path_list, res_path_list

def score_precision_recall_f1(query_file, res_file, doc_pos_mode=None):
    
    true_path_list, res_path_list = _read_query_and_res_files(query_file, res_file, doc_pos_mode)

    precision_list, recall_list, f1_list = [], [], []
    false_positives_list = []
    false_negatives_list = []

    for i in range(len(true_path_list)):
        if len(res_path_list[i]):
            precision = len(set(true_path_list[i]).intersection(set(res_path_list[i]))) / len(res_path_list[i])
        else:
            precision = 0
        recall = len(set(true_path_list[i]).intersection(set(res_path_list[i]))) / len(true_path_list[i])
        if precision + recall:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0
        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)

        false_positives = set(res_path_list[i]).difference(set(true_path_list[i]))
        false_positives_list.append(false_positives)
        false_negatives = set(true_path_list[i]).difference(set(res_path_list[i]))
        false_negatives_list.append(false_negatives)

    return precision_list, recall_list, f1_list, false_positives_list, false_negatives_list
    

def precision_recall_at_k(query_file, res_file, k_values=[1, 5, 10, 15], doc_pos_mode=None):
    true_path_list, res_path_list = _read_query_and_res_files(query_file, res_file, doc_pos_mode)

    p_at_k = defaultdict(list)
    r_at_k = defaultdict(list)

    n_results = []
    n_golds = []

    for i, true_paths in enumerate(true_path_list):
        res_paths = res_path_list[i]

        for k in k_values:
            if k == k_values[0]:
                n_results.append(len(res_paths))
                n_golds.append(len(true_paths))

            if not res_paths:
                precision = 0
            else:
                precision = len(set(true_paths).intersection(set(res_paths[:k]))) / len(res_paths[:k])
            p_at_k[k].append(precision)

            recall = len(set(true_paths).intersection(set(res_paths[:k]))) / len(true_paths)
            r_at_k[k].append(recall)

    return p_at_k, r_at_k, n_results, n_golds

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("persona", help="Persona name")
    ap.add_argument("--query_dir", default="./data/query")
    ap.add_argument("--filter_frequent_2_and_3_token_queries", action="store_true", default=False)
    ap.add_argument("--eval_document_position", action="store_true", default=False)
    args = ap.parse_args()

    persona_name = args.persona
    query_dir = args.query_dir

    if args.filter_frequent_2_and_3_token_queries:
        query_file = f'{query_dir}/{persona_name}_ff23_query.json'
        res_file = f'{query_dir}/{persona_name}_wiki_search_results_ff23.json'
    else:
        query_file = f'{query_dir}/{persona_name}_query.json'
        res_file = f'{query_dir}/{persona_name}_wiki_search_results.json'

    framenet_eval = False
    if query_dir.strip("/").endswith("fn_queries"):
        framenet_eval = True
        query_file = query_file.replace("_query.json", "_q2g.json")

    if args.eval_document_position:
        assert framenet_eval, "Document position evaluation only available with FrameNet-based queries"
        query_file = query_file.replace("_q2g.json", "_q2g_plus.json")
        doc_pos_modes = ["document", "sentence", "frame"]
    else:
        doc_pos_modes = [None]

    for dpm in doc_pos_modes:

        print(dpm)

        precision_list, recall_list, f1_list, false_positives_list, false_negatives_list = \
            score_precision_recall_f1(
                query_file=query_file,
                res_file=res_file,
                doc_pos_mode=dpm
            )

        print("==================")
        print("PREC/REC/F1 (full)")    
        print(round(np.mean(precision_list) * 100), round(np.std(precision_list) * 100))
        print(round(np.mean(recall_list) * 100), round(np.std(recall_list) * 100))
        print(round(np.mean(f1_list) * 100), round(np.std(f1_list) * 100))
        print("==================")
        print()
        print("==================")
        k_values = [30, 20, 10, 5]
        print("PREC/REC @ K")
        p_at_k, r_at_k, n_results, n_golds = precision_recall_at_k(
            query_file=query_file,
            res_file=res_file,
            k_values=k_values,
            doc_pos_mode=dpm
        )
        avg_n_results = sum(n_results) / len(n_results)
        avg_n_golds = sum(n_golds) / len(n_golds)
        print(f"avg #results: {avg_n_results:.2f}\navg #golds: {avg_n_golds:.2f}\n")

        for k in k_values:
            print(f"K = {k}")
            if not p_at_k[k]:
                print("(empty array, no score!)\n")
                continue
            precision = sum(p_at_k[k]) / len(p_at_k[k])
            recall = sum(r_at_k[k]) / len(r_at_k[k])

            print(f"Prec@{k}={round(precision * 100)}")
            print(f" Rec@{k}={round(recall * 100)}")
            print()   
        print("==================")


        error_file = f"{query_dir}/{persona_name}.errors.jsonl"
        if args.filter_frequent_2_and_3_token_queries:
            error_file = f"{query_dir}/{persona_name}_ff23.errors.jsonl"
        if dpm:
            error_file = error_file.replace(".errors.jsonl", f".errors.{dpm}.jsonl")

        with open(error_file, "w", encoding="utf-8") as f:
            for fp, fn in zip(false_positives_list, false_negatives_list):
                f.write(json.dumps({"false_positives": list(fp), "false_negatives": list(fn)}) + os.linesep)
