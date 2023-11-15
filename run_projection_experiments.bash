# Script for running the evaluation pipeline with different projection settings

# replace path by appropriate dirs
export PERSONAS_DIR=$(realpath "../datasets/personas")
export MODEL_DIR=$(realpath "../datasets/projection_experiments/output")

# spm model
export SPM_VOCAB="./app/api/models/en/enwiki.vocab"
export SPM_MODEL="./app/api/models/en/enwiki.model"

PROJECTION_OPTIONS=(

    ../datasets/projection_experiments/proj_mat/128/float/111.npy
)

for option in "${PROJECTION_OPTIONS[@]}"
do
    # clear up index and db
    rm -f app/static/db/app.db
    rm -fr app/static/pods/*npz

    # start the server, wait until it's running
    export PROJ_PATH=$option
    { python run.py & } &> _tmp_pears_logs.txt
    sleep 5

    pushd evaluate/

    echo "-------------"
    echo "projection path: $option"

    # echo "indexing: 0-hr"
    curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/0-hr/index.html&keyword=0-hr" > /dev/null

    # echo "evaluating: 0-hr"
     python eval.py 0_hr --pod 0-hr --query_dir $PERSONAS_DIR/personas_queries/

    # echo "indexing: 1-accountant"
    # curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/1-accountant/index.html&keyword=1-accountant" > /dev/null

    # echo "evaluating: 1-accountant"
    # python eval.py 1_accountant --pod 1-accountant --query_dir $PERSONAS_DIR/personas_queries/

    # echo "indexing: 2-news"
    # curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/2-news/index.html&keyword=2-news" > /dev/null

    # echo "evaluating: 2-news"
    # python eval.py 2_news --pod 2-news --query_dir $PERSONAS_DIR/personas_queries/

    # echo "indexing: 3-moviesummary"
    # curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/3-moviesummary/index.html&keyword=3-moviesummary" > /dev/null

    # echo "evaluating: 3-moviesummary"
    # python eval.py 3_moviesummary --pod 3-moviesummary --query_dir $PERSONAS_DIR/personas_queries/

    echo "-------------"
    echo

    popd

    # stop the server
    kill %1  # kill last process

done