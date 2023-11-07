import argparse
import requests
import json
from collections import OrderedDict
from tqdm import tqdm
import sys, os

def search_queries(query_file, pod="home"):
    queries = []
    with open(query_file) as f:
        for line in f:
            queries.append(list(json.loads(line).keys())[0])

    results = []
    for q in tqdm(queries):
        url = 'http://localhost:9090'
        params = {
            "q": q,
            "pods": pod
        }
        try:
            response_text = requests.get(url, params=params).text
            response = json.loads(response_text, object_pairs_hook=OrderedDict)
        except json.decoder.JSONDecodeError as e:
            response = {'': ''}
            print(url, params, response_text)
            raise e
        retrieve_urls = []
        for u in response.keys():
            if u:
                retrieve_urls.append(u.split('/')[-1])
        results.append({q: retrieve_urls})
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("persona", help="Persona name")
    ap.add_argument("--query_dir", default="./data/query")
    ap.add_argument("--pod", default="home", help="PeARS pod name (keyword)")
    ap.add_argument("--filter_frequent_2_and_3_token_queries", action="store_true", default=False)
    args = ap.parse_args()

    persona_name = args.persona
    query_dir = args.query_dir

    if args.filter_frequent_2_and_3_token_queries:
        query_file = f'{query_dir}/{persona_name}_ff23_query.json'
        results_file = f'{query_dir}/{persona_name}_wiki_search_results_ff23.json'
    else:
        query_file = f'{query_dir}/{persona_name}_query.json'
        results_file = f'{query_dir}/{persona_name}_wiki_search_results.json'
    
    if query_dir.strip("/").endswith("fn_queries"):
        framenet_eval = True
        query_file = query_file.replace("_query.json", "_q2g.json")
    
    res = search_queries(query_file, pod=args.pod)
    with open(results_file, 'w') as f:
        for row in res:
            json_str = json.dumps(row)
            f.write(json_str + '\n')
