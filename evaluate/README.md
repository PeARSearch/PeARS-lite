# Evaluating PeARS search performance for particular data distributions

This directory contains scripts and data for evaluating the search algorithms on some artificial *persona*, i.e. a user with a specific filesystem distribution. Preprocessing scripts for creating personae and generating queries sets can also be found here. Adding the persona to the system's data is done using the *mk_user.py* script referenced in the top directory of this repo. 

In what follows we will assume that we have already created some persona called *0_hr*. 


## Scripts contained in this repository

*json_dataset.py* and *pdf2txt.py* are used for preprocessing raw datasets, for example to transform pdf and json formats to txt format.

*utils.py*: utility functions.

*create_query.py*: generate a gold standard to evaluate the system. This is achieved by reading a preprocessed dataset, and producing pairs of the form *(q,D)*, where *q* is a query and *D* is the set of documents containing *q*.

*search.py*: search for all the queries by sending request to the PeARS Flask app.

*score_res.py*: read the search results and compute the performance of the search function.


## To create a new query file for a new dataset:

Run the *preprocess.py* script with a persona name as an argument (e.g python3 *preprocess.py* 0_hr)

## Add the new dataset to PeARS:

### Traditional method
By default, datasets are all indexed in the same pod. Before doing a new evaluation experiment, make sure that the previous indexes are deleted:

```
rm -f app/static/db/app.db
rm -fr app/static/pods/*npz
```

To fully clean up the installation (optional), you can also delete the user directory: `rm -rf app/static/testdocs/$USER/` where `$USER` is the user corresponding to the previously evaluated datasets.

Once you have a clean install, add the new dataset to the system:

```
python3 mkuser.py 0-hr $DATA_DIR/personas/$USER/?
curl localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/$USER/index.html
```

where `$USER` is the username for the new dataset. 

### Separated pods (new!)
To avoid having to delete the entire database after each experiment, use a separate pod for each persona. 

```
python3 mkuser.py 0-hr $DATA_DIR/personas/$USER/?
curl "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/$USER/index.html&keyword=$USER"
```

(In this example, the pod keyword corresponds to the persona's user name -- this is not strictly necessary but recommended. Don't forget the quotes around the url to escape the '&')

If you use this method, be sure to also pass the pod argument to `search.py` (or to `eval.py`).

## To evaluate the system for a particular persona:

Run the eval.py file with persona name as an argument (e.g python3 eval.py 0_hr)

