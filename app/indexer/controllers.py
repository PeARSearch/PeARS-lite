# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
import logging
import joblib
import numpy as np
from scipy import sparse
from math import ceil
from flask import (Blueprint,
                   flash,
                   request,
                   render_template,
                   Response)

from app.api.models import Urls
from app.indexer.neighbours import neighbour_urls
from app.indexer import mk_page_vector, spider
from app.utils import readDocs, readUrls, readBookmarks, get_language
from app.utils_db import pod_from_file
from app.indexer.htmlparser import extract_links
from os.path import dirname, join, realpath, isfile

dir_path = dirname(dirname(realpath(__file__)))

# Define the blueprint:
indexer = Blueprint('indexer', __name__, url_prefix='/indexer')


# Set the route and accepted methods
@indexer.route("/", methods=["GET", "POST"])
def index():
    num_db_entries = len(Urls.query.all())
    if request.method == "GET":
        return render_template(
            "indexer/index.html", num_entries=num_db_entries)


'''
 Controllers for various ways to index
 (from file, from url, from crawl)
'''


@indexer.route("/from_docs", methods=["POST"])
def from_docs():
    print("DOC FILE:", request.files['file_source'])
    if request.files['file_source'].filename[-4:] == ".txt":
        keyword = request.form['docs_keyword']
        keyword, lang = get_language(keyword)
        file = request.files['file_source']
        file.save(join(dir_path, "docs_to_index.txt"))
        f = open(join(dir_path, "keyword_lang.txt"), 'w')
        f.write(keyword+'::'+lang+'\n')
        f.close()
        return render_template('indexer/progress_docs.html')


@indexer.route("/from_file", methods=["POST"])
def from_file():
    print("FILE:", request.files['file_source'])
    if request.files['file_source'].filename[-4:] == ".txt":
        file = request.files['file_source']
        # filename = secure_filename(file.filename)
        file.save(join(dir_path, "urls_to_index.txt"))
        return render_template('indexer/progress_file.html')


@indexer.route("/from_bookmarks", methods=["POST"])
def from_bookmarks():
    print("FILE:", request.files['file_source'])
    if "bookmarks" in request.files['file_source'].filename:
        keyword = request.form['bookmark_keyword']
        keyword, lang = get_language(keyword)
        file = request.files['file_source']
        file.save(join(dir_path, "bookmarks.html"))
        urls = readBookmarks(join(dir_path,"bookmarks.html"), keyword)
        print(urls)
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        for u in urls:
            f.write(u + ";" + keyword + ";" + lang +"\n")
        f.close()
        return render_template('indexer/progress_file.html')


@indexer.route("/from_url", methods=["POST"])
def from_url():
    if request.form['url'] != "":
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        u = request.form['url']
        keyword = request.form['url_keyword']
        keyword, lang = get_language(keyword)
        print(u, keyword, lang)
        f.write(u + ";" + keyword + ";" + lang +"\n")
        f.close()
        return render_template('indexer/progress_url.html', url=u)


@indexer.route("/from_share", methods=["POST"])
def from_share():
    print("FILE:", request.files['file_source'])
    if request.files['file_source'].filename[-6:] == ".share":
        file = request.files['file_source']
        pod_name, main_lang, m, titles, urls = joblib.load(file)
        sparse.save_npz(join(pod_dir,pod_name), m)
        pod_from_file(pod_name, main_lang, np.sum(m,axis=0))
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        for u in urls:
            f.write(u + ";" + pod_name + ";" + lang +"\n")
        f.close()
        return render_template('indexer/progress_file.html')


'''
Controllers for progress pages.
One controller per ways to index (file, crawl).
The URL indexing uses same progress as file.
'''


@indexer.route("/progress_file")
def progress_file():
    logging.debug("Running progress file")
    def generate():
        urls, keywords, langs, errors = readUrls(join(dir_path, "urls_to_index.txt"))
        if errors:
            logging.error('Some URLs could not be processed')
        if not urls or not keywords or not langs:
            logging.error('Invalid file format')
            yield "data: 0 \n\n"
        kwd = keywords[0]
        pod_name = kwd+'.npz'
        pod_dir = join(dir_path,'static','pods')
        print("POD DIR",pod_dir)
        if not isfile(join(pod_dir,pod_name)):
            print("Making 0 CSR matrix")
            pod = np.zeros((1,10000))
            pod = sparse.csr_matrix(pod)
            sparse.save_npz(join(pod_dir,pod_name), pod)
        c = 0
        for url, kwd, lang in zip(urls, keywords, langs):
            success, podsum = mk_page_vector.compute_vectors(url, kwd, lang)
            if success:
                pod_from_file(kwd, lang, podsum)
            else:
                logging.error("Error accessing the URL")
            c += 1
            yield "data:" + str(int(c / len(urls) * 100)) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

@indexer.route("/progress_docs")
def progress_docs():
    logging.debug("Running progress local file")
    def generate():
        kwd = ''
        lang='en'
        urls, titles, snippets = readDocs(join(dir_path, "docs_to_index.txt"))
        f = open(join(dir_path, "keyword_lang.txt"), 'r')
        for line in f:
            kwd,lang = line.rstrip('\n').split('::')
        pod_name = kwd+'.npz'
        pod_dir = join(dir_path,'static','pods')
        if not isfile(join(pod_dir,pod_name)):
            print("Making 0 CSR matrix")
            pod = np.zeros((1,10000))
            pod = sparse.csr_matrix(pod)
            sparse.save_npz(join(pod_dir,pod_name), pod)
        c = 0
        for url, title, snippet in zip(urls, titles, snippets):
            print(url,title)
            mk_page_vector.compute_vectors_local_docs(url, title, snippet, kwd)
            pod_from_file(kwd, 'en')
            c += 1
            print('###', str(ceil(c / len(urls) * 100)))
            yield "data:" + str(ceil(c / len(urls) * 100)) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

