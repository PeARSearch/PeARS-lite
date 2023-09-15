import os
import sys

persona = sys.argv[1]

os.system('python ./search.py '+ persona)
os.system('python ./score_res.py '+ persona)