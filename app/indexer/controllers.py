# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
import logging
import joblib
import numpy as np
from scipy import sparse
from pandas import read_csv
from math import ceil, isnan
from flask import (Blueprint,
                   flash,
                   request,
                   render_template,
                   Response)
from app import VEC_SIZE, LANG
from app.api.models import Urls
from app.indexer.neighbours import neighbour_urls
from app.indexer import mk_page_vector, spider
from app.utils import readDocs, readUrls, readBookmarks, get_language, init_pod, init_podsum
from app.utils_db import pod_from_file
from app.indexer.htmlparser import extract_links
from app.indexer.posix import posix_doc
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
    if Urls.query.count() == 0:
        init_podsum()

    filename = request.files['file_source'].filename
    print("DOC FILE:", filename)
    if filename[-4:] == ".txt":
        keyword = request.form['docs_keyword']
        doctype = request.form['docs_type']
        if doctype == '' or doctype.isspace():
            doctype = 'doc'
        else:
            doctype = request.form['docs_type'].lower()
        keyword, lang = get_language(keyword)
        print("LANGUAGE:",lang)
        file = request.files['file_source']
        file.save(join(dir_path, "docs_to_index.txt"))
        f = open(join(dir_path, "file_source_info.txt"), 'w')
        f.write(filename+'::'+keyword+'::'+lang+'::'+doctype+'\n')
        f.close()
        return render_template('indexer/progress_docs.html')


@indexer.route("/from_csv", methods=["POST"])
def from_csv():
    if Urls.query.count() == 0:
        init_podsum()

    filename = request.files['file_source'].filename
    print("CSV FILE:", filename)
    if filename[-4:] == ".csv":
        keyword = request.form['csv_keyword']
        doctype = request.form['docs_type']
        if doctype == '' or doctype.isspace():
            doctype = 'csv'
        else:
            doctype = request.form['docs_type'].lower()
        keyword, lang = get_language(keyword)
        print("LANGUAGE:",lang)
        file = request.files['file_source']
        file.save(join(dir_path, "spreadsheet_to_index.csv"))
        f = open(join(dir_path, "file_source_info.txt"), 'w')
        f.write(filename+'::'+keyword+'::'+lang+'::'+doctype+'\n')
        f.close()
        return render_template('indexer/progress_csv.html')


@indexer.route("/from_file", methods=["POST"])
def from_file():
    if Urls.query.count() == 0:
        init_podsum()

    print("FILE:", request.files['file_source'])
    if request.files['file_source'].filename[-4:] == ".txt":
        file = request.files['file_source']
        # filename = secure_filename(file.filename)
        file.save(join(dir_path, "urls_to_index.txt"))
        return render_template('indexer/progress_file.html')


@indexer.route("/from_bookmarks", methods=["POST"])
def from_bookmarks():
    if Urls.query.count() == 0:
        init_podsum()

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
    if Urls.query.count() == 0:
        init_podsum()

    if request.form['url'] != "":
        f = open(join(dir_path, "urls_to_index.txt"), 'w')
        u = request.form['url']
        keyword = request.form['url_keyword']
        keyword, lang = get_language(keyword)
        print(u, keyword, lang)
        f.write(u + ";" + keyword + ";" + lang +"\n")
        f.close()
        return render_template('indexer/progress_url.html', url=u)



'''
Controllers for progress pages.
One controller per ways to index (file, crawl).
The URL indexing uses same progress as file.
'''


@indexer.route("/progress_file")
def progress_file():
    print("Running progress file")
    def generate():
        urls, keywords, langs, errors = readUrls(join(dir_path, "urls_to_index.txt"))
        if errors:
            logging.error('Some URLs could not be processed')
        if not urls or not keywords or not langs:
            logging.error('Invalid file format')
            yield "data: 0 \n\n"
        kwd = keywords[0]
        init_pod(kwd)
        c = 0
        for url, kwd, lang in zip(urls, keywords, langs):
            print("CONTROLLER",url)
            success, podsum, text, doc_id = mk_page_vector.compute_vectors(url, kwd, lang)
            if success:
                posix_doc(text, doc_id, kwd)
                pod_from_file(kwd, lang, podsum)
            c += 1
            data = ceil(c / len(urls) * 100)
            yield "data:" + str(data) + "\n\n"
        yield "data:" + "Finished!" + "\n\n"
    return Response(generate(), mimetype='text/event-stream')

@indexer.route("/progress_docs")
def progress_docs():
    logging.debug("Running progress local file")
    def generate():
        kwd = ''
        lang = LANG
        doctype = 'doc'
        urls, titles, snippets = readDocs(join(dir_path, "docs_to_index.txt"))
        f = open(join(dir_path, "file_source_info.txt"), 'r')
        for line in f:
            source, kwd, lang, doctype = line.rstrip('\n').split('::')
        init_pod(kwd)
        c = 0
        for url, title, snippet in zip(urls, titles, snippets):
            success, podsum, text, doc_id = mk_page_vector.compute_vectors_local_docs(url, doctype, title, snippet, kwd, lang)
            if success:
                posix_doc(text, doc_id, kwd)
                pod_from_file(kwd, lang, podsum)
            c += 1
            data = ceil(c / len(urls) * 100)
            yield "data:" + str(data) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')


@indexer.route("/progress_csv")
def progress_csv():
    logging.debug("Running progress local csv")
    def generate():
        kwd = ''
        lang = LANG
        doctype = 'csv'
        try:
            df = read_csv(join(dir_path, "spreadsheet_to_index.csv"), delimiter=';', encoding="utf-8")
        except:
            print("CSV Encoding is not utf-8")
            df = read_csv(join(dir_path, "spreadsheet_to_index.csv"), delimiter=';', encoding="iso-8859-1")

        f = open(join(dir_path, "file_source_info.txt"), 'r')
        for line in f:
            source, kwd, lang, doctype = line.rstrip('\n').split('::')
        init_pod(kwd)
        c = 0
        columns = list(df.columns)
        table = df.to_numpy()
        for i in range(table.shape[0]):
            row = table[i]
            print(row, type(row[0]))
            if isinstance(row[0],float) and isnan(row[0]):
                continue
            title = source.replace('.csv','').title()+': '+str(row[0])+' ['+str(i)+']'
            url = source+'#'+title
            snippet = ''
            for i in range(len(columns)):
                value = str(row[i]).replace('/',' / ')
                snippet+=str(columns[i])+': ' +value+'. '
            print(url,title)
            success, podsum, text, doc_id = mk_page_vector.compute_vectors_local_docs(url, doctype, title, snippet, kwd, lang)
            if success:
                posix_doc(text, doc_id, kwd)
                pod_from_file(kwd, lang, podsum)
            c += 1
            data = ceil(c / table.shape[0] * 100)
            yield "data:" + str(data) + "\n\n"

    return Response(generate(), mimetype='text/event-stream')

