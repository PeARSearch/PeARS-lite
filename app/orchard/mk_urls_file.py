# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

from app.api.models import Urls, Pods
from app import db
from os.path import dirname, realpath, join, basename
from os import remove
import numpy as np
from scipy.sparse import vstack, load_npz
from collections import Counter

dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')


def make_shareable_pod(keyword):
    url_keyword = keyword.replace(' ', '_')
    hfile = join(dir_path, "static", "pods", url_keyword + ".pears")
    lang = db.session.query(Pods).filter_by(name=keyword).first().language
    f_out = open(hfile,'w')
    for url in db.session.query(Urls).filter_by(pod=keyword).all():
        print(url.title)
        f_out.write(url.url+';'+keyword+';'+lang+'\n')
    f_out.close()
    return hfile


def del_pod(keyword):
    print("Deleting pod")
    for url in db.session.query(Urls).filter_by(keyword=keyword).all():
        print("Deleting "+url.url+" "+url.pod)
        db.session.delete(url)
        db.session.commit()
    for pod in db.session.query(Pods).filter_by(description=keyword).all():
        if "localhost" in pod.url:
            db.session.delete(pod_entry)
            db.session.commit()
    os.remove(join(pod_dir,keyword+'.npz')) 
    os.remove(join(pod_dir,keyword+'.pos')) 

