# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
from flask import Blueprint, jsonify, request

import numpy as np
from scipy.sparse import csr_matrix, vstack, save_npz, load_npz
from os.path import dirname, join, realpath, basename
from app.utils_db import pod_from_file
from app.api.models import Urls, Pods
from app import db


# Define the blueprint:
api = Blueprint('api', __name__, url_prefix='/api')

dir_path = dirname(dirname(realpath(__file__)))
pod_dir = join(dir_path,'static','pods')


@api.route('/pods/')
def return_pods():
    return jsonify(json_list=[p.serialize for p in Pods.query.all()])


@api.route('/pods/<pod>/')
def return_pod(pod):
    pod = pod.replace('+', ' ')
    p = db.session.query(Pods).filter_by(name=pod).first()
    return jsonify(p.serialize)


@api.route('/urls/')
def return_urls():
    return jsonify(json_list=[i.serialize for i in Urls.query.all()])


@api.route('/urls/delete', methods=["GET","POST"])
def return_delete():
    path = request.args.get('path')
    try:
        u = db.session.query(Urls).filter_by(url=path).first()
        pod = u.pod
        vid = int(u.vector)

        #Remove document row from .npz matrix
        pod_m = load_npz(join(pod_dir,pod+'.npz'))
        m1 = pod_m[:vid]
        m2 = pod_m[vid+1:]
        pod_m = vstack((m1,m2)) 
        save_npz(join(pod_dir,pod+'.npz'),pod_m)

        #Correct indices in DB
        urls = db.session.query(Urls).filter_by(pod=pod).all()
        for url in urls:
            if int(url.vector) > vid:
                url.vector = str(int(url.vector)-1) #Decrease ID now that matrix row has gone
            db.session.add(url)
            db.session.commit()
        
        #Recompute pod summary
        podsum = np.sum(pod_m, axis=0)
        p = db.session.query(Pods).filter_by(name=pod).first()
        pod_from_file(pod, p.language, podsum)
        db.session.delete(u)
        db.session.commit()
    except:
        return "Deletion failed"
    return "Deleted document with vector id"+str(vid)


@api.route('/urls/move', methods=["GET","POST"])
def return_rename():
    src = request.args.get('src')
    target = request.args.get('target')
    try:
        u = db.session.query(Urls).filter_by(url=src).first()

        #Rename in DB
        src_name = basename(src)
        target_name = basename(target)
        u.url = target
        if u.title == src_name:
            u.title = target_name

        db.session.add(u)
        db.session.commit()
    except:
        return "Moving failed"
    return "Moved file "+src+" to "+target
        
