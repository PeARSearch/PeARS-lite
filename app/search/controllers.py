# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
from flask import Blueprint, request, render_template, send_from_directory
from flask import current_app

# Import the database object from the main app module
from app.api.models import Urls
from app.search import score_pages

# Import matrix manipulation modules
import numpy as np
from scipy import sparse

# Import utilities
import re
import logging
from os.path import dirname, join, realpath, isfile
from app.utils import init_podsum, beautify_title, beautify_snippet
from app import EXPERT_ADD_ON, OWN_BRAND

LOG = logging.getLogger(__name__)

# Define the blueprint:
search = Blueprint('search', __name__, url_prefix='')

dir_path = dirname(dirname(dirname(realpath(__file__))))
pod_dir = join(dir_path,'app','static','pods')


@search.context_processor
def inject_brand():
    return dict(own_brand=OWN_BRAND)

@search.route('/')
@search.route('/index')
def index():  
    results = []
    internal_message = ""
    if Urls.query.count() == 0:
        internal_message = "Hey there! It looks like you're here\
         for the first time :) To understand how to use PeARS,\
         go to the FAQ (link at the top of the page)."
        init_podsum()

    query = request.args.get('q')
    if not query:
        LOG.info("No query")
        return render_template("search/index.html", internal_message=internal_message, own_brand=OWN_BRAND)
    else:
        displayresults = []
        query = query.lower()
        pears = ['0.0.0.0']
        results, pods = score_pages.run(query, pears)
        if not results:
            pears = ['no pear found :(']
            results = [{'url':None, 'title':None, 'snippet':'No pages found', 'doctype':None, 'notes':None}]
        for r in results:
            r['title'] = beautify_title(r['title'], r['doctype'])
            r['snippet'] = beautify_snippet(r['snippet'], r['img'], query)
            displayresults.append(list(r.values()))

        #return render_template('search/results.html', pears=pods, query=query, results=displayresults)
        return render_template('search/results.html', pears=[], query=query, results=displayresults, expert=EXPERT_ADD_ON, own_brand=OWN_BRAND)

@search.route('/experts/<kwd>/<idx>/')
def experts(kwd,idx):  
    print(idx,kwd)
    displayresults = []
    results, pods = score_pages.score_experts(idx,kwd)
    if not results:
        pears = ['no pear found :(']
        results = [{'url':None, 'title':None, 'snippet':'No pages found', 'doctype':None, 'notes':None}]
    for r in results:
        r['title'] = beautify_title(r['title'], r['doctype'])
        displayresults.append(list(r.values()))
    return render_template('search/results.html', pears=[], query="-", results=displayresults, expert=EXPERT_ADD_ON, own_brand=OWN_BRAND)

@search.route('/html_cache/<path:filename>')
def custom_static(filename):
    return send_from_directory('html_cache', filename)
