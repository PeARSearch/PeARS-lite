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

In the root of the repo, run:

    python3 run.py



## Usage

The installation contains four sample .txt documents in the static folder, to provide a toy example. When the app is running, these documents are accessible at:

```
http://localhost:8080/static/testdocs/letter_to_grandma.txt
http://localhost:8080/static/testdocs/novel_draft.txt
http://localhost:8080/static/testdocs/invoice_23_05_2023.txt
http://localhost:8080/static/testdocs/invoice_24_05_2023.txt
```

To index a document on localhost:

```
curl localhost:8080/indexer/from_url?url=http://localhost:8080/static/testdocs/invoice_24_05_2023.txt
```

Example searches:

```
curl localhost:8080?q=invoice
curl localhost:8080?q=novel+moss
```

The search function returns json objects containing all information about the selected URLs in the database. For instance, searching for the word 'invoice' returns the following two documents:

```
{
  "http://localhost:8080/static/testdocs/invoice_23_05_2023.txt": {
    "cc": "False", 
    "date_created": "2023-05-24 10:16:59", 
    "date_modified": "2023-05-24 10:16:59", 
    "id": "4", 
    "notes": "None", 
    "pod": "home", 
    "snippet": "Dear customer-\n\nThank you for your order- and for supporting local artists. Your parrot sculpture has been dispatched.  I allow myself to send you this invoice- for the amount of 2000 EUR. It is payab", 
    "title": "invoice_23_05_2023.txt", 
    "url": "http://localhost:8080/static/testdocs/invoice_23_05_2023.txt", 
    "vector": "4"
  }, 
  "http://localhost:8080/static/testdocs/invoice_24_05_2023.txt": {
    "cc": "False", 
    "date_created": "2023-05-24 07:23:39", 
    "date_modified": "2023-05-24 07:23:39", 
    "id": "3", 
    "notes": "None", 
    "pod": "home", 
    "snippet": "Esteemed customer-\n\nI thank you for your order. It has been a pleasure doing business with you. I allow myself to send you this invoice- for the amount of 200EUR. It is payable with the next four week", 
    "title": "invoice_24_05_2023.txt", 
    "url": "http://localhost:8080/static/testdocs/invoice_24_05_2023.txt", 
    "vector": "3"
  }
}
```

The indexer now has an authorisation header, currently set up as the placeholder 'TOK:1234':

https://github.com/PeARSearch/PeARS-lite/blob/d3a8471d8930f971d20f56f7820d1b214e84b108/app/indexer/htmlparser.py#L14
