json_dataset.py and pdf2txt.py: used for preprocessing the raw datasets,
for example: transform pdf and json format to text format.

utils.py: utility functions.

create_query.py: read the preprocessed dataset, select from the files
the pairs of query - file paths containing the query.

search.py: search for all the queries by sending request to flask.

score_res.py: read the search results and compute the performance of the search/

## To create a new query file for a new dataset:

1. Run the function preprocess_dataset in utils.py
2. Run the script create_query.py. It takes times, up to 1 2 hours for the news and moviescripts dataset.
