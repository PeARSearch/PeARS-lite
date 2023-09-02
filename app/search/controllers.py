# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org>, 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Import flask dependencies
from flask import Blueprint, request, render_template, send_from_directory, make_response
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField

# Import the database object from the main app module
from app import app
from app.api.models import Urls
from app.search import score_pages

# Import matrix manipulation modules
import numpy as np
from scipy import sparse

# Import utilities
import re
import requests
import logging
from os.path import dirname, join, realpath, isfile
from flask import jsonify, Response
from app.utils import init_podsum

LOG = logging.getLogger(__name__)

# Define the blueprint:
search = Blueprint('search', __name__, url_prefix='')

dir_path = dirname(dirname(dirname(realpath(__file__))))
pod_dir = join(dir_path,'app','static','pods')

class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')
    submit = SubmitField('Submit')

@search.route('/user', methods=['POST','GET'])
def user():  
    results = []
    if Urls.query.count() == 0:
        init_podsum()

    query = request.args.get('q')
    if not query:
        LOG.info("No query")
        return render_template("search/user.html")
    else:
        results = []
        query = query.lower()
        pears = ['0.0.0.0']
        results, pods = score_pages.run(query, pears)
        print(results)
        r = app.make_response(jsonify(results))
        r.mimetype = "application/json"
        return r


@search.route('/anonymous', methods=['POST','GET'])
def anonymous():  
    results = []
    if Urls.query.count() == 0:
        init_podsum()

    query = request.args.get('q')
    if not query:
        LOG.info("No query")
        return render_template("search/anonymous.html")
    else:
        results = []
        query = query.lower()
        pears = ['0.0.0.0']
        results, pods = score_pages.run(query, pears)
        print(results)
        r = app.make_response(jsonify(results))
        r.mimetype = "application/json"
        return r



@search.route('/', methods=['GET','POST'])
@search.route('/index', methods=['GET','POST'])
def index():
    access_token = request.cookies.get('OMD_SESSION_ID')  
    if not access_token:
        return render_template('search/anonymous.html')
    else:
        url = 'http://localhost:9191/api' #TODO: change URL to OMD endpoint
        data = {'action': 'getUserInfo', 'session_id': access_token}
        resp = requests.post(url, data=data)
        username = resp.json()['username']
        return render_template('search/user.html', username=username)



@search.route('/login', methods=['GET', 'POST'])
def login():
    # Declare the login form using FlaskForm library
    form = LoginForm(request.form)
    # Flask message injected into the page, in case of any errors
    msg = None
    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():
        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str)
        # send authorization message to on my disk
        url = 'http://localhost:9191/api' #TODO: change URL to OMD endpoint
        data = {'action': 'signin', 'username': username, 'password': password}
        resp = requests.post(url, data=data)
        access_token = resp.cookies.get('OMD_SESSION_ID')
        print(resp.json())
        data = {'action': 'getUserInfo', 'session_id': access_token}
        resp = requests.post(url, data=data)
        username = resp.json()['username']
        return render_template('search/user.html', welcome="Welcome "+username)
    else:
       msg = "Unknown user"
       return render_template( 'search/login.html', form=form, msg=msg)

