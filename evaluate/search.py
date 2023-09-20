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
        url = 'http://localhost:9090?q=' + str(q).replace(' ', '+')
        params = {
            "q": q.replace(" ", "+"), # TODO check  if conversion ' ' -> '+' is not done already automatically?
            "pods": pod
        }
        try:
            response = json.loads(requests.get(url, params=params).text, object_pairs_hook=OrderedDict)
        except json.decoder.JSONDecodeError:
            response = {'': ''}
            print(url)
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
    args = ap.parse_args()

    persona_name = args.persona
    query_dir = args.query_dir
    res = search_queries(f'{query_dir}/{persona_name}_query.json', pod=args.pod)
    with open(f'{query_dir}/{persona_name}_wiki_search_results.json', 'w') as f:
        for row in res:
            json_str = json.dumps(row)
            f.write(json_str + '\n')
