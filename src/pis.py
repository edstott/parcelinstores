#!/usr/bin/env python

import urllib2, re

# Credential file
LOGIN = 'credentials'
# URL of 
STORES = 'https://intranet.ee.ic.ac.uk/storesweb/parcels/GoodsInWeb.html'

# Read user credentials from the credential file
with open(LOGIN) as login:
		(username, password) = login.read().split(' ')

# Create a password manager instance for the stores URL and load with user credentials
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, STORES, username, password.decode('base64'))

# Create and build an auth handler with this password manager and 
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)

# Install the opener
urllib2.install_opener(opener)

# Open up the site and scrape the html
response = urllib2.urlopen(STORES)
html = response.read()

# 