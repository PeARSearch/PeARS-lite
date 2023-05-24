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

    sudo apt-get update

    sudo apt-get install python3-setuptools

    sudo apt-get install python3-pip

    sudo pip install virtualenv

Then change into the PeARS-lite directory:

    cd PeARS-lite

Then run:

    virtualenv env && source env/bin/activate


##### 3. Install the build dependencies:

From the PeARS-lite directory, run:

    pip install -r requirements.txt



##### 5. Run your pear!

In the root of the repo, run:

    python3 run.py



## Usage

The installation contains three sample .txt documents in the static folder, to provide a toy example. When the app is running, these documents are accessible at:

```
http://localhost:8080/static/testdocs/letter_to_grandma.txt
http://localhost:8080/static/testdocs/novel_draft.txt
http://localhost:8080/static/testdocs/invoice_24_05_2023.txt
```

To index a document on localhost:

```
curl localhost:8080/indexer/from_url?url=http://localhost:8080/static/testdocs/invoice_24_05_2023.txt
```

To search:

```
curl localhost:8080/index?q=invoice
```
