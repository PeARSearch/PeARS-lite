# SPDX-FileCopyrightText: 2023 PeARS Project <community@pearsproject.org>
#
# SPDX-License-Identifier: AGPL-3.0-only

from os.path import abspath, dirname, join
from pathlib import Path

# Statement for enabling the development environment
DEBUG = True

# Define the application directory
BASE_DIR = abspath(dirname(__file__))
Path(join(BASE_DIR,'app/static/db')).mkdir(parents=True, exist_ok=True)

# Define the database - we are working with
# SQLite for this example
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(BASE_DIR, 'app/static/db/app.db')
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"

SQLALCHEMY_TRACK_MODIFICATIONS = False
