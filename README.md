<!--
SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org> 

SPDX-License-Identifier: AGPL-3.0-only
-->

# PeARS Lite - OMD integration


## What and why

**What:** This branch of *PeARS-lite* is dedicated to the version of PeARS Lite used in the context of the project *On My Disk: search integration*. A description of the project can be found [on this page](https://www.ngisearch.eu/view/Events/FirstTenSearchersAnnounced). We are grateful to the Next Generation Internet programme of the European Commission for the financial support given to this project (see credits at the bottom of this README).

**Why:** This PeARS version is tailored for use with the [On My Disk](https://onmydisk.com/) private cloud solution. It includes features for indexing and search over a user's decentralised filesystem.




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

    sudo apt install python3-virtualenv

Then change into the PeARS-lite directory:

    cd PeARS-lite

Then run:

    virtualenv env && source env/bin/activate


##### 3. Install the build dependencies:

From the PeARS-lite directory, run:

    pip install -r requirements.txt



##### 5. Run your pear!

If you are running/testing PeARS-lite locally (as opposed to the OMD server), first export the LOCAL_RUN variable and run the toy authentification server provided in *test-auth.py*:

```
export LOCAL_RUN=True
python3 test-auth.py  & python3 run.py 
```

If you are the OMD admin, run:

```
export LOCAL_RUN=False
python3 run.py
```

You should now see the login page of PeARS at http://localhost:9090/. You can sign in, either with your On My Disk credentials on the server, or if you are running locally, with a test user called Kim (username: kim, password: pwd).


NB: whenever you want to come back to a clean install, manually delete your database and pods:

```
rm -f app/static/db/app.db
rm -fr app/static/pods/*npz
```


## API Usage

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

## Credits


<img src="https://pearsproject.org/images/NGI.png" width='400px'/>

Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Commission. Neither the European Union nor the granting authority can be held responsible for them. Funded within the framework of the NGI Search project under grant agreement No101069364.
