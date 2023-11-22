import json
import os

import numpy as np


def compare_overlap(sim_file, q2g_file, raw_dir):
    precision_lists = {
        "D": [],
        "S": [],
        "F": []
    }

    with open(sim_file, encoding="utf-8") as fs, open(q2g_file, encoding="utf-8") as fq:
        sim_data = json.load(fs) # sim data can be loaded directly, q2g data is read line by line
        for (query, sim_docs), q2g_line in zip(sim_data.items(), fq): 
            q2g_item = json.loads(q2g_line)
            doc_matches = {
                os.path.basename(doc_path)
                for doc_path in q2g_item[query]["document_matches"]
            }
            sentence_matches = {
                os.path.basename(m["doc"])
                for m in q2g_item[query]["sentence_matches"]
            }
            frame_matches = {
                os.path.basename(m["doc"])
                for m in q2g_item[query]["frame_matches"]
            }

            overlapping_dm = list(set(sim_docs).intersection(doc_matches))
            overlapping_sm = list(set(sim_docs).intersection(sentence_matches))
            overlapping_fm = list(set(sim_docs).intersection(frame_matches))
            precision_d = len(overlapping_dm) / len(sim_docs)
            precision_s = len(overlapping_sm) / len(sim_docs)
            precision_f = len(overlapping_fm) / len(sim_docs)
            precision_lists["D"].append(precision_d)
            precision_lists["S"].append(precision_s)
            precision_lists["F"].append(precision_f)

            snippets = []
            for od in overlapping_dm:
                with open(f"{raw_dir}/{od}") as odf:
                    snippets.append(odf.read()[:100].strip().replace("\n", " "))

            print("QUERY", query)
            print(f"PRECISION (d) {precision_d:.2f}")
            print(f"PRECISION (s) {precision_s:.2f}")
            print(f"PRECISION (f) {precision_f:.2f}")
            print("OVERLAP", overlapping_dm)
            print("SNIPPETS", snippets)
            print()
    
    print("---")
    print(f"AVG PREC (d) {np.mean(precision_lists['D']):.2f}")
    print(f"AVG PREC (s) {np.mean(precision_lists['S']):.2f}")
    print(f"AVG PREC (f) {np.mean(precision_lists['F']):.2f}")
    

if __name__ == "__main__":
    # compare_overlap(
    #     "../../datasets/personas/personas_sbert_top10/2_news_preprocessed_res.json",
    #     "../../datasets/personas/personas_fn_queries/2_news_q2g_plus.json",
    #     "../../datasets/personas/personas_raw/2_news"
    # )
    compare_overlap(
        "../../datasets/personas/personas_sbert_top10/1_accountant_preprocessed_res.json",
        "../../datasets/personas/personas_fn_queries/1_accountant_q2g_plus.json",
        "../../datasets/personas/personas_raw/1_accountant"
    )
