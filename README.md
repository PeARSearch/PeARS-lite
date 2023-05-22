<!--
SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org> 

SPDX-License-Identifier: AGPL-3.0-only
-->

# PeARS Lite


## What and why

*PeARS Lite* is a bare-bone version of PeARS which will allow you to index and search Web document in your language, locally and robustly.


## Installation and Setup


##### 1. Clone this repo on your machine:

```
    git clone https://github.com/PeARSearch/PeARS-orchard.git
```

##### 2. **Optional step** Setup a virtualenv in your directory.

If you haven't yet set up virtualenv on your machine, please install it via pip:

    sudo apt-get update

    sudo apt-get install python3-setuptools

    sudo apt-get install python3-pip

    sudo pip install virtualenv

Then change into the PeARS-orchard directory:

    cd PeARS-for-toppix

Then run:

    virtualenv env && source env/bin/activate


##### 3. Install the build dependencies:

From the PeARS-orchard directory, run:

    pip install -r requirements.txt



##### 5. Run your pear!

In the root of the repo, run:

    python3 run.py



## Usage

Now, go to your browser at *localhost:8080*. You should see the search page for PeARS. You don't have any pages indexed yet, so go to the F.A.Q. page (link at the top of the page) and follow the short instructions to get you going!

