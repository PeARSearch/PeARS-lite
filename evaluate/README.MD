json_dataset.py and pdf2txt.py: used for preprocessing the raw datasets,
for example: transform pdf and json format to text format.

utils.py: utility functions.

create_query.py: read the preprocessed dataset, select from the files
the pairs of query - file paths containing the query.

search.py: search for all the queries by sending request to flask.

score_res.py: read the search results and compute the performance of the search/

## To create a new query file for a new dataset:

Run the preprocess.py file with persona name as an argument (e.g python preprocess.py 0_hr)

## To evaluate the system for particular persona:

Run the eval.py file with persona name as an argument (e.g python eval.py 0_hr)

