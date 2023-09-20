<!--
SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org> 

SPDX-License-Identifier: AGPL-3.0-only
-->

# PeARS Lite - OMD integration


## What and why

This version of *PeARS Lite* is the one that will be integrated with the On My Disk framework.


## Installation and Setup


##### 1. Clone this repo on your machine:

```
    git clone -b ngi-search https://github.com/PeARSearch/PeARS-lite.git
```

##### 2. **Optional step** Setup a virtualenv in your directory.

If you haven't yet set up virtualenv on your machine, please install it via pip:

    sudo apt update

    sudo apt install python3-setuptools

    sudo apt install python3-pip

    sudo pip install virtualenv

Then change into the PeARS-lite directory:

    cd PeARS-lite

Then run:

    virtualenv env && source env/bin/activate


##### 3. Install the build dependencies:

From the PeARS-lite directory, run:

    pip install -r requirements.txt



##### 5. Run your pear!

If you are running/testing PeARS-lite locally (as opposed to the OMD server), first uncomment lines 38-39 in app/indexer/spider.py:

```
if url[-1] == '/': #For local test only
            url = join(url,'index.html')
```

Then, in the root of the repo, run:

    python3 run.py

NB: whenever you want to come back to a clean install, manually delete your database and pods:

```
rm -f app/static/db/app.db
rm -fr app/static/pods/*npz
```


## Usage

To provide a toy example, the installation contains sample documents in the static folder, organised in folders as follows:

```
http://localhost:9090/static/testdocs/
    |_index.html
    |_tester/
        |_index.html
        |_localhost.localdomain
            |_index.html
            |_Downloads
                |_index.html
                |_sample2.txt
                |_sample3.txt
                |_sample4.txt
            |_Music
                |_index.html
            |_Pictures
                |_index.html
            |_Videos
                |_index.html
```
			

NB: on the OMD server, the index.html files will be created on-the-fly at runtime.
 

To recursively crawl from base url:

```
curl localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/tester/index.html
```

By default, this will index the crawled pages in the `"home"` pod. However, you can also specify a pod of your choice: 

```
curl "localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/tester/index.html&keyword=$POD"
```

where `$POD` is the name of the pod (existing or new) that you want to use. 

Example searches:

```
curl localhost:9090?q=grandma
curl localhost:9090?q=theory+of+everything
```

The search function returns json objects containing all information about the selected URLs in the database. For instance, searching for the word 'grandma' returns the following two documents:

```
{
  "http://localhost:9090/static/testdocs/tester/localhost.localdomain/Downloads/sample2.txt": {
    "cc": "False", 
    "date_created": "2023-07-31 14:24:42", 
    "date_modified": "2023-07-31 14:24:42", 
    "description": "Telling grandma about the roses.", 
    "id": "7", 
    "pod": "home", 
    "snippet": "Hi Grandma,  I hope you are doing well. We have planted new roses in our garden, but they still don't look as good as yours!  Lots of love.  ", 
    "title": "Letter to grandma", 
    "url": "http://localhost:9090/static/testdocs/tester/localhost.localdomain/Downloads/sample2.txt", 
    "vector": "7"
  }
}

```

It is also possible to restrict queries to one or more specific pods. The `pod` parameter accepts either a specific pod name or a comma-separated list. If the parameter is not specified, the system will search through all pods.

For example:

```
curl localhost:9090?q=grandma # search in all pods
curl localhost:9090?q=grandma?pod=home # search only in the 'home' pod
curl localhost:9090?q=grandma?pod=accountant,home # search only in the 'accountant' and 'home' pods
```

## Adding your own data

To test PeARS-lite with your own data, you will have to set up a new user in the static/testdocs folder. The following illustrates this process with a toy example, to be run from the base directory.

First, we will assume that we have a folder somewhere on our computer, containing .txt files. For the sake of illustration, we will reuse the *static/testdocs/tester/localhost.localdomain/Downloads/* directory in this example, but you can use your own.

Second, we will create a new user with a *Documents* directory, where we will copy the .txt files from our chosen folder. There is a script in the root of the repo to do exactly this. You can feed it a new username and the path to the folder with your .txt documents. This script also sets up the directory structure required to match the OMD server. So for instance, let us create a new user called *myuser*, and copy some sample files to their space, using the content of our previous *Downloads* directory:

```
python3 mkuser.py myuser app/static/testdocs/tester/localhost.localdomain/Downloads/
```

The result of this call is a new *app/static/testdocs/myuser/* directory, with some .txt files in the *localhost.localdomain/Documents/* folder of that user.

Once we have done this, we can index the files of this new user: 

```
curl localhost:9090/indexer/from_crawl?url=http://localhost:9090/static/testdocs/myuser/index.html
```

And finally we can search as before:

```
curl localhost:9090?q=grandma
```

NB: again, if you would like to start from a clean install, do not forget to manually delete the existing index:

```
rm -f app/static/db/app.db
rm -fr app/static/pods/*npz
```
