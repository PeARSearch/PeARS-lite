import os
import argparse
import json
import numpy as np
import sys

def score_precision_recall_f1(query_file, res_file):
    true_path_list = []
    with open(query_file) as f:
        for line in f:
            true_path_list.append(list(json.loads(line).values())[0])

    res_path_list = []
    with open(res_file) as f:
        for line in f:
            res_path_list.append(list(json.loads(line).values())[0])

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


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("persona", help="Persona name")
    ap.add_argument("--query_dir", default="./data/query")
    args = ap.parse_args()

    persona_name = args.persona
    query_dir = args.query_dir

    precision_list, recall_list, f1_list, false_positives_list, false_negatives_list = \
        score_precision_recall_f1(
            query_file=f'{query_dir}/{persona_name}_query.json',
            res_file=f'{query_dir}/{persona_name}_wiki_search_results.json')
    
    print(round(np.mean(precision_list) * 100), round(np.std(precision_list) * 100))
    print(round(np.mean(recall_list) * 100), round(np.std(recall_list) * 100))
    print(round(np.mean(f1_list) * 100), round(np.std(f1_list) * 100))

    with open(f"{query_dir}/{persona_name}.errors.jsonl", "w", encoding="utf-8") as f:
        for fp, fn in zip(false_positives_list, false_negatives_list):
            f.write(json.dumps({"false_positives": list(fp), "false_negatives": list(fn)}) + os.linesep)
