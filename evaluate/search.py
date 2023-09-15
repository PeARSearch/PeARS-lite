import requests
import json
from collections import OrderedDict
from tqdm import tqdm
import sys, os

def search_queries(query_file):
    queries = []
    with open(query_file) as f:
        for line in f:
            queries.append(list(json.loads(line).keys())[0])

    results = []
    for q in tqdm(queries):
        url = 'http://localhost:9090?q=' + str(q).replace(' ', '+')
        try:
            response = json.loads(requests.get(url).text, object_pairs_hook=OrderedDict)
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
    persona_name = sys.argv[1]
    res = search_queries(f'./data/query/{persona_name}_query.json')
    with open(f'./data/query/{persona_name}_wiki_search_results.json', 'w') as f:
        for row in res:
            json_str = json.dumps(row)
            f.write(json_str + '\n')
