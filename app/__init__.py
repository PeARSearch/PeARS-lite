# SPDX-FileCopyrightText: 2022 PeARS Project, <community@pearsproject.org> 
#
# SPDX-License-Identifier: AGPL-3.0-only

import os
import logging
import numpy as np

# Import flask and template operators
from flask import Flask, render_template
from flask_admin import Admin

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

# Experimental SentencePiece versions -- call via subprocess instead of via Python library
SPM_EXPERIMENTAL = os.environ.get("SPM_EXPERIMENTAL", "false").lower() == "true"
SPM_EXPERIMENTAL_PATH = os.environ.get("SPM_EXPERIMENTAL_PATH", None)  # path to binaries of experimental SPM
assert SPM_EXPERIMENTAL_PATH or not SPM_EXPERIMENTAL, "If SPM_EXPERIMENTAL is set to True, SPM_EXPERIMENTAL_PATH must be given"
print(f"SPM_EXPERIMENTAL={SPM_EXPERIMENTAL}")
print(f"SPM_EXPERIMENTAL_PATH={SPM_EXPERIMENTAL_PATH}")

# Get paths to SentencePiece model and vocab
lang = 'en' # hardcoded for now
SPM_DEFAULT_VOCAB_PATH = f'app/api/models/{lang}/{lang}wiki.vocab'
spm_vocab_path = os.environ.get("SPM_VOCAB", SPM_DEFAULT_VOCAB_PATH)
SPM_DEFAULT_MODEL_PATH = f'app/api/models/{lang}/{lang}wiki.model'
spm_model_path = os.environ.get("SPM_MODEL", SPM_DEFAULT_MODEL_PATH)

# Global variable: apply pre-tokenization rules
do_pretokenization = os.environ.get("DO_PRETOK", "false").lower() == "true"
pretok_path = os.environ.get("PRETOK_PATH", None)
print(f"do_pretokenization={do_pretokenization}, use files from: {pretok_path}")

# Global variable: add EOF symbol post-tokenization
add_posttok_eof = os.environ.get("ADD_POSTTOK_EOF", "false").lower() == "true"
print(f"add_posttok_eof={add_posttok_eof}")

# Global variables: use snippet scoring system
USE_SNIPPET_SCORES = os.environ.get("USE_SNIPPET_SCORES", "false").lower() == "true"
SNIPPET_COMPLETENESS_THRESHOLD = float(os.environ.get("SNIPPET_COMPLETENESS_THRESHOLD", "0.75"))
SNIPPET_OVERLAP_THRESHOLD = float(os.environ.get("SNIPPET_OVERLAP_THRESHOLD", "0.75"))
print(f"USE_SNIPPET_SCORES={USE_SNIPPET_SCORES}, completeness threshold set to {SNIPPET_COMPLETENESS_THRESHOLD}, overlap threshold set to {SNIPPET_OVERLAP_THRESHOLD}")

# Global variable: cache pods
CACHE_PODS = os.environ.get("CACHE_PODS", "false").lower() == "true"
pod_cache = {}
print(f"CACHE_PODS={CACHE_PODS}")

# Global variable: use inverse index
POSINDEX = os.environ.get("POSINDEX")

# Global variable: projection matrix
PROJ_MAT = np.load(os.environ.get("PROJ_PATH"))
POD_DIM = PROJ_MAT.shape[1]

# Define vector size
from app.indexer.vectorizer import read_vocab

print(f"Loading SPM vocab from '{spm_vocab_path}' ...")
vocab, reverse_vocab, _ = read_vocab(spm_vocab_path)
if add_posttok_eof:
    vocab.update({f"{w}▁": v + len(vocab) for w, v in vocab.items()})
    reverse_vocab = {v: w for w, v in vocab.items()}
VEC_SIZE = len(vocab)

def configure_logging():
    # register root logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.INFO)


configure_logging()

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)


# Import a module / component using its blueprint handler variable (mod_auth)
from app.indexer.controllers import indexer as indexer_module
from app.api.controllers import api as api_module
from app.search.controllers import search as search_module
from app.pod_finder.controllers import pod_finder as pod_finder_module
from app.orchard.controllers import orchard as orchard_module
from app.pages.controllers import pages as pages_module
from app.settings.controllers import settings as settings_module

# Register blueprint(s)
app.register_blueprint(indexer_module)
app.register_blueprint(api_module)
app.register_blueprint(search_module)
app.register_blueprint(pod_finder_module)
app.register_blueprint(orchard_module)
app.register_blueprint(pages_module)
app.register_blueprint(settings_module)
# ..

# Build the database:
# This will create the database file using SQLAlchemy
#db.drop_all()
with app.app_context():
    db.create_all()

from flask_admin.contrib.sqla import ModelView
from app.api.models import Pods, Urls

# Flask and Flask-SQLAlchemy initialization here

admin = Admin(app, name='PeARS DB', template_mode='bootstrap3')

class UrlsModelView(ModelView):
    list_template = 'admin/pears_list.html'
    column_exclude_list = ['vector','cc']
    column_searchable_list = ['url', 'title', 'description', 'pod']
    column_editable_list = ['description']
    can_edit = True
    page_size = 50
    form_widget_args = {
        'vector': {
            'readonly': True
        },
        'date_created': {
            'readonly': True
        },
        'date_modified': {
            'readonly': True
        },
    }

class PodsModelView(ModelView):
    list_template = 'admin/pears_list.html'
    column_exclude_list = ['DS_vector','word_vector']
    column_searchable_list = ['url', 'name', 'description', 'language']
    can_edit = True
    page_size = 50
    form_widget_args = {
        'DS_vector': {
            'readonly': True
        },
        'word_vector': {
            'readonly': True
        },
        'date_created': {
            'readonly': True
        },
        'date_modified': {
            'readonly': True
        },
    }

admin.add_view(PodsModelView(Pods, db.session))
admin.add_view(UrlsModelView(Urls, db.session))
