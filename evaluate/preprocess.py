import os
import sys

persona = sys.argv[1]

os.system('python ./utils.py '+ persona)
os.system('python ./create_query.py '+ persona)