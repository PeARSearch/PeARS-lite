# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
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
from app.utils import readDocs, readUrls, get_language, init_podsum
from app.utils_db import pod_from_file
from app.indexer.htmlparser import extract_links, extract_html
from os.path import dirname, join, realpath, isfile

dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')

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
 (from file, from url)
'''

@indexer.route("/from_omd_index", methods=["GET","POST"])
def from_omd_index():
    keyword = "home" #hard-coded
    lang = "en" #hard-coded

    def process_links(omd_html):
        if omd_html[-1] == '/':
            omd_html+='index.html'
        links = extract_links(omd_html)
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        for u in links:
            f.write(u + ";" + keyword + ";" + lang +"\n")
        f.close()

    if request.method =="POST":
        print("DOC FILE:", request.form['url'])
        omd_html = request.form['url']
        process_links(omd_html)
        return render_template('indexer/progress_crawl.html')
    else:
        print("DOC FILE:", request.args['url'])
        omd_html = request.args['url']
        process_links(omd_html)
        return progress_crawl()
        


@indexer.route("/from_docs2", methods=["POST"])
def from_docs2():
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


@indexer.route("/from_file", methods=["GET","POST"])
def from_file():
    if request.method == "POST":
        print("FILE:", request.files['file_source'])
        if request.files['file_source'].filename[-4:] == ".txt":
            file = request.files['file_source']
            file.save(join(dir_path, "urls_to_index.txt"))
            return render_template('indexer/progress_file.html')
    if request.method == "GET":
        file = request.args['file_source']
        file.save(join(dir_path, "urls_to_index.txt"))
        return render_template('indexer/progress_file.html')


@indexer.route("/from_url", methods=["GET", "POST"])
def from_url():
    if request.method == "POST":
        if request.form['url'] != "":
            f = open(join(dir_path, "urls_to_index.txt"), 'w')
            u = request.form['url']
            keyword = 'home' #hard-coded
            lang = 'en' #hard-coded for now
            f.write(u + ";" + keyword + ";" + lang +"\n")
            f.close()
            return render_template('indexer/progress_file.html')
    if request.method == "GET":
        u = request.args['url']
        keyword = 'home' #hard-coded
        lang = 'en' #hard-coded for now
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        f.write(u + ";" + keyword + ";" + lang +"\n")
        f.close()
        return progress_file()



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
        print("PROGRESS FILE",urls,keywords,langs)
        if errors:
            logging.error('Some URLs could not be processed')
        if not urls or not keywords or not langs:
            logging.error('Invalid file format')
            yield "data: 0 \n\n"
        kwd = 'home' #hard-coded
        pod_name = kwd+'.npz'
        pod_dir = join(dir_path,'static','pods')
        
        #Checking matrix files
        if not isfile(join(pod_dir,'podsum.npz')):
            init_podsum()
        print("POD DIR",pod_dir)
        if not isfile(join(pod_dir,pod_name)):
            print("Making 0 CSR matrix")
            pod = np.zeros((1,10000))
            pod = sparse.csr_matrix(pod)
            sparse.save_npz(join(pod_dir,pod_name), pod)
        c = 0
        print(len(urls),"URLS to index")
        for url, kwd, lang in zip(urls, keywords, langs):
            success, podsum = mk_page_vector.compute_vectors(url, kwd, lang)
            if success:
                pod_from_file(kwd, lang, podsum)
            else:
                logging.error("Error accessing the URL")
            c += 1
            yield "data:" + str(int(c / len(urls) * 100)) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

@indexer.route("/progress_crawl")
def progress_crawl():
    print("Running progress crawl")
    urls, keywords, langs, errors = readUrls(join(dir_path, "urls_to_index.txt"))
    if urls:
        url = urls[0]
    kwd = 'home' #hard-coded
    lang = 'en'  #hard-coded
    pod_name = kwd+'.npz'
    pod_dir = join(dir_path,'static','pods')

    #Checking matrix files
    if not isfile(join(pod_dir,'podsum.npz')):
        init_podsum()
    if not isfile(join(pod_dir,pod_name)):
        print("Making 0 CSR matrix")
        pod = np.zeros((1,10000))
        pod = sparse.csr_matrix(pod)
        sparse.save_npz(join(pod_dir,pod_name), pod)

    def generate():
        # netloc = urlparse(url).netloc
        all_links = [url]
        stack = spider.get_links(url,200)
        indexed = 0
        while len(stack) > 0:
            all_links.append(stack[0])
            print("Processing", stack[0])
            success, podsum = mk_page_vector.compute_vectors(stack[0], kwd, lang)
            if success:
                pod_from_file(kwd, lang, podsum)
                stack.pop(0)
                indexed += 1
                yield "data:" + str(indexed) + "\n\n"
            else:
                stack.pop(0)
        yield "data: " + "Finished!" + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

@indexer.route("/progress_docs")
def progress_docs():
    logging.debug("Running progress local file")
    def generate():
        kwd = 'home' #hard-coded - change if needed
        lang='en' #hard-coded - change in multilingual version
        urls, titles, snippets = readDocs(join(dir_path, "docs_to_index.txt"))
        pod_name = kwd+'.npz'
        pod_dir = join(dir_path,'static','pods')

        #Checking matrix files
        if not isfile(join(pod_dir,'podsum.npz')):
            init_podsum()
        if not isfile(join(pod_dir,pod_name)):
            print("Making 0 CSR matrix")
            pod = np.zeros((1,10000))
            pod = sparse.csr_matrix(pod)
            sparse.save_npz(join(pod_dir,pod_name), pod)

        c = 0
        for url, title, snippet in zip(urls, titles, snippets):
            print(url,title)
            success, podsum = mk_page_vector.compute_vectors_local_docs(url, title, snippet, kwd, lang)
            pod_from_file(kwd, lang, podsum)
            c += 1
            print('###', str(ceil(c / len(urls) * 100)))
            yield "data:" + str(ceil(c / len(urls) * 100)) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

