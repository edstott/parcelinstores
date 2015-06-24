#!/usr/bin/env python

import urllib2, re
from bs4 import BeautifulSoup

# CAS members to watch
CAS = ['LEVINE', 'STOTT', 'DAVIS', 'OGDEN', 'WIJEYASINGHE', 'HUNG', 'FOK']
# Credential file
LOGIN = '.credentials'
# URL of stores parcel tracker
STORES = 'https://intranet.ee.ic.ac.uk/storesweb/parcels/GoodsInWeb.html'
# Colour of new and collected parcels
NEW = {'bgcolor':'Beige'}
COLLECTED = {'bgcolor':'LightSteelBlue'}

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

# Open up the stores parcel tracker site, try again if times out
response = None
while response is None:
	try:
		response = urllib2.urlopen(STORES, timeout = 1)
		print response
	except urllib2.URLError:
		print 'Connection timed out, try again'
		pass

# Read the site and pass to BeautifulSoup
html = response.read()
soup = BeautifulSoup(html)

# Find the first table in the page
table = soup.find("table")
# Find all of the rows (tr) objects with NEW attributes
for row in table.findAll('tr', NEW):
	# Find all the cells/data (td) in this row
	cells = row.findAll('td')
	# Strip the tags from each cell and convert contents to utf8
	cells = [cell.text.strip().encode('utf8') for cell in cells]
	# Check the row isn't blank before proceeding further
	if cells:
		if (any(name.upper() in CAS for name in cells[4].split(' '))):
			print 'CAS matches:', cells





