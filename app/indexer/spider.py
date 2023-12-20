# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

import xmltodict
import requests
from collections import OrderedDict
from os.path import join, dirname, realpath
from app.indexer.htmlparser import extract_html
from app import LOCAL_RUN, AUTH_TOKEN

dir_path = dirname(dirname(realpath(__file__)))


def omd_parse(current_url):
    print("\n\nRunning OMD parse on", current_url)
    links = []
    fout = open(join(dir_path,'docs_to_index.txt'),'a')
    try:
        xml = requests.get(current_url, timeout=10, headers={'Authorization': AUTH_TOKEN}, stream =True).raw
        parse = xmltodict.parse(xml.read())
    except:
        print("Request failed. Moving on.")
        return links
    docs = parse['omd_index']['doc']
    print("PARSE:",parse)
    if type(docs) is not list:
        docs = [docs]
    for doc in docs:
        urldir = '/'.join(current_url.split('/')[:-1])

        # URL
        if doc['@url'][0] == '/':
            url = doc['@url'][1:]
        else:
            url = doc['@url']
        url = join(urldir, url)
        print("# DOC URL:", url)
        print("LOCAL",LOCAL_RUN)
        if LOCAL_RUN:
            if url[-1] == '/': #For local test only
                url = join(url,'index.html')

        # CONTENT TYPE
        try:
            print("# DOC CONTENTTYPE: ", doc['@contentType'])
            content_type = doc['@contentType']
            if content_type in ['folder','desktop']: #Folder / desktop won't have any other info, so continue
                links.append(url)
                continue
        except:
            print(" DOC CONTENTTYPE: No contentType")


        # TITLE
        try:
            print("# DOC TITLE:", doc['title'])
            title = doc['title']
        except:
            print("# DOC TITLE: No title")
        if title == None:
            title = ''
        #print("<doc title='"+title+"' url='"+url+"'>\n")
        fout.write("<doc title='"+title+"' url='"+url+"'>\n")

        # DESCRIPTION
        try:
            print("# DOC DESCRIPTION:", doc['description'][:100])
            description = doc['description']
            print("\t"+description+"\n")
            fout.write("{{DESCRIPTION}} "+description+"\n")
        except:
            print("# DOC DESCRIPTION: No description")
    
        # CONTENT
        if content_type in ['text/plain','text/html']:
            title, body_str, snippet, cc, error = extract_html(url)
            if not error:
                print("# DOC BODY:", body_str[:100])
                fout.write("{{BODY}} "+body_str+"\n")
        else:
            print("# DOC BODY: Skipping request: content is neither text/plain nor text/html.")

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
                #print(link,pages_visited)
                #print(link,pages_to_visit)
                #print(link,urldir)
                if link not in pages_visited and link not in pages_to_visit and '#' not in link: # and urldir in link:
                    #print("Found href:",link)
                    pages_to_visit.append(link)
        except:
            print(">> ERROR: Failed visiting current url!")


