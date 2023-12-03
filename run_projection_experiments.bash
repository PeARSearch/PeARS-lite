# Script for running the evaluation pipeline with different projection settings

# replace path by appropriate dirs
export PERSONAS_DIR=$(realpath "../datasets/personas")
export MODEL_DIR=$(realpath "../datasets/projection_experiments/output")

# spm model
export SPM_VOCAB="./app/api/models/en/enwiki.vocab"
export SPM_MODEL="./app/api/models/en/enwiki.model"

PROJECTION_OPTIONS=(

    ../datasets/projection_experiments/proj_mat/256/fasttext_min10/111.npy
    ../datasets/projection_experiments/proj_mat/256/fasttext_min10/222.npy
    ../datasets/projection_experiments/proj_mat/256/fasttext_min10/333.npy
    ../datasets/projection_experiments/proj_mat/256/fasttext_min10/444.npy
    ../datasets/projection_experiments/proj_mat/256/fasttext_min10/555.npy
)

for option in "${PROJECTION_OPTIONS[@]}"
do
    # clear up index and db
    rm -f app/static/db/app.db
    rm -fr app/static/pods/*npz

    # start the server, wait until it's running
    export PROJ_PATH=$option
    { python run.py & } &> _run_logs_hr.txt
    sleep 5

    pushd evaluate/

    echo "-------------"
    echo "projection path: $option"

    echo "indexing: 0-hr"
    curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/0_hr/index.html&keyword=0_hr" > /dev/null

    echo "evaluating: 0-hr"
    python eval.py 0_hr --pod 0_hr --query_dir $PERSONAS_DIR/personas_queries/

    echo "-------------"
    echo

    popd

    # stop the server
    kill %1  # kill last process

done

#for option in "${PROJECTION_OPTIONS[@]}"
#do
#    # clear up index and db
#    rm -f app/static/db/app.db
#    rm -fr app/static/pods/*npz
#
#    # start the server, wait until it's running
#    export PROJ_PATH=$option
#    { python run.py & } &> _run_logs_accountant.txt
#    sleep 5
#
#    pushd evaluate/
#
#    echo "-------------"
#    echo "projection path: $option"
#
#    echo "indexing: 1-accountant"
#    curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/1_accountant/index.html&keyword=1_accountant" > /dev/null
#
#    echo "evaluating: 1-accountant"
#    python eval.py 1_accountant --pod 1_accountant --query_dir $PERSONAS_DIR/personas_queries/
#
#    echo "-------------"
#    echo
#
#    popd
#
#    # stop the server
#    kill %1  # kill last process
#
#done

#for option in "${PROJECTION_OPTIONS[@]}"
#do
#    # clear up index and db
#    rm -f app/static/db/app.db
#    rm -fr app/static/pods/*npz
#
#    # start the server, wait until it's running
#    export PROJ_PATH=$option
#    { python run.py & } &> /dev/null
#    sleep 5
#
#    pushd evaluate/
#
#    echo "-------------"
#    echo "projection path: $option"
#
#    echo "indexing: 2_news"
#    curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/2_news/index.html&keyword=0_hr" > /dev/null
#
#    echo "evaluating: 2_news"
#    python eval.py 2_news --pod 2_news --query_dir $PERSONAS_DIR/personas_queries/
#
#    echo "-------------"
#    echo
#
#    popd
#
#    # stop the server
#    kill %1  # kill last process
#
#done
#
#for option in "${PROJECTION_OPTIONS[@]}"
#do
#    # clear up index and db
#    rm -f app/static/db/app.db
#    rm -fr app/static/pods/*npz
#
#    # start the server, wait until it's running
#    export PROJ_PATH=$option
#    { python run.py & } &> /dev/null
#    sleep 5
#
#    pushd evaluate/
#
#    echo "-------------"
#    echo "projection path: $option"
#
#    echo "indexing: 3_moviesummary"
#    curl -# "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/3_moviesummary/index.html&keyword=1_accountant" > /dev/null
#
#    echo "evaluating: 3_moviesummary"
#    python eval.py 3_moviesummary --pod 3_moviesummary --query_dir $PERSONAS_DIR/personas_queries/
#
#    echo "-------------"
#    echo
#
#    popd
#
#    # stop the server
#    kill %1  # kill last process
#
#done
