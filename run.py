# SPDX-FileCopyrightText: 2023 PeARS Project, <community@pearsproject.org> 
#
# SPDX-License-Identifier: AGPL-3.0-only

# Run a test server.

from app import app
app.run(host='localhost', port=8080, debug=True)
