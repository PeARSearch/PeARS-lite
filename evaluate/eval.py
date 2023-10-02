import argparse
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("persona", help="Persona name")
ap.add_argument("--query_dir", default="./data/query")
ap.add_argument("--pod", default="home", help="PeARS pod name (keyword)")
# ap.add_argument("--spm_model", default=None)
args = ap.parse_args()

persona = args.persona
query_dir = args.query_dir
pod = args.pod
# spm_model = args.spm_model

os.system(f"python ./search.py {persona} --query_dir {query_dir} --pod {pod}")
# os.system(f"python ./score_res.py {persona} --query_dir {query_dir} --spm_model {spm_model}")
os.system(f"python ./score_res.py {persona} --query_dir {query_dir}")