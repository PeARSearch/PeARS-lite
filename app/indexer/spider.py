# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import xmltodict
import requests
from collections import OrderedDict
from os.path import join, dirname, realpath
from app.indexer.htmlparser import extract_html

dir_path = dirname(dirname(realpath(__file__)))


def omd_parse(current_url):
    print("\n\nRunning OMD parse on", current_url)
    links = []
    fout = open(join(dir_path,'docs_to_index.txt'),'a')

    xml = requests.get(current_url, stream =True).raw
    parse = xmltodict.parse(xml.read())
    docs = parse['omd_index']['doc']
    print("PARSE:",parse, type(docs))
    if type(docs) is not list:
        docs = [docs]
    print(docs)
    for doc in docs:
        urldir = '/'.join(current_url.split('/')[:-1])

        # URL
        #try:
        if doc['@url'][0] == '/':
            url = doc['@url'][1:]
        else:
            url = doc['@url']
        url = join(urldir, url)
        print("# DOC URL", url)
        #if url[-1] == '/': #For local test only
        #    url = join(url,'index.html')
        links.append(url)
        #except:
        #    print("\t--- No valid url")
        #    continue

        # CONTENT TYPE
        try:
            print("# DOC CONTENTTYPE", urldir, doc['@contentType'])
            content_type = doc['@contentType']
            if content_type == 'folder':
                continue
        except:
            print("\t--- No contentType")

        # TITLE
        try:
            print("# DOC TITLE", urldir, doc['title'])
            title = doc['title']
        except:
            print("\t--- No title")
        if title == None:
            title = ''
        print("<doc title='"+title+"' url='"+url+"'>\n")
        fout.write("<doc title='"+title+"' url='"+url+"'>\n")

        # DESCRIPTION
        try:
            print("# DOC DESCRIPTION", urldir, doc['description'])
            description = doc['description']
            print("\t"+description+"\n")
            fout.write("\t"+description+"\n")
        except:
            print("\t--- No description")
    
        # CONTENT
        #try:
        title, body_str, snippet, cc, error = extract_html(url)
        if not error:
            print("# BODY", body_str)
            fout.write(body_str+"\n")
        #except:
        #    print("\t--- Failed to extract text")

        fout.write("</doc>\n")
    fout.close()

    print("\n NEW LINKS:",links)
    return links

def write_docs(base_url):  
    if base_url[-5:] == ".html":
        urldir = '/'.join(base_url.split('/')[:-1])
    else:
        urldir = base_url
    pages_to_visit = [base_url]
    pages_visited = []

    #Initialise docs_to_index
    fout = open(join(dir_path,'docs_to_index.txt'),'w')
    fout.close()

    print("Starting crawl from",base_url)
    while pages_to_visit != []:
        # Start from base url
        print("Pages to visit",pages_to_visit)
        url = pages_to_visit[0]
        pages_visited.append(url)
        pages_to_visit = pages_to_visit[1:]
        try:
            print("\n\n#### Scraping:", url)
            links = omd_parse(url)
            for link in links:
                print(link,pages_visited)
                print(link,pages_to_visit)
                print(link,urldir)
                if link not in pages_visited and link not in pages_to_visit and '#' not in link: # and urldir in link:
                    print("Found href:",link)
                    pages_to_visit.append(link)
        except:
            print(">> ERROR: Failed visiting current url!")


