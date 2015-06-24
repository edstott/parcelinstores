#!/usr/bin/env python

import urllib2, ssl
from bs4 import BeautifulSoup
import time

# CAS members to watch
CAS = ['LEVINE,J', 'STOTT,E', 'DAVIS,J', 'OGDEN,P', 'WIJEYASINGHE,M', 'HUNG,E', 'HOGGETT,J']
# Build current and new dictionaries
cas_prev = {x:[] for x in CAS}
cas_new = {x:[] for x in CAS}

# Credential file
LOGIN = '.credentials'
# URL of stores parcel tracker
STORES = 'https://intranet.ee.ic.ac.uk/storesweb/parcels/GoodsInWeb.html'
# Colour of new and collected parcels
NEW = {'bgcolor':'Beige'}
COLLECTED = {'bgcolor':'LightSteelBlue'}
SLEEP = 10

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

# Set up for the main loop
first_loop = True
ring_bell = False

# Loop forever, sleeping between iterations
while True:
	# Open up the stores parcel tracker site, try again if times out
	response = None
	while response is None:
		try:
			response = urllib2.urlopen(STORES, timeout = 1)
		except urllib2.URLError, ssl.SSLError:
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
			# Only process further if the row isn't blank
			if cells:
				for person in CAS:
					(surname, initial) = person.split(',')
					# Check if the surname
					if any([True if name.upper() == surname else False for name in cells[4].split(' ')]):
						# Check the initial - only works if CAS members don't have same surname forename initials!
						if any([True if name.upper()[0] == initial else False for name in cells[4].split(' ')]):
							cas_new[person].append(cells[0])

	# Now loop through the data and see what has change - ring the bell for new parcels
	# Only do this after the first iteration of the loop
	if not first_loop:
		for person in CAS:
			new_parcels = [parcel for parcel in cas_new[person] if parcel not in cas_prev[person]]
			print person, new_parcels
			if len(new_parcels) > 0:
				ring_bell = True

	if ring_bell:
		print "Ringing the bell"
		ring_bell = False

	# Clean up before sleeping
	cas_prev = cas_new
	first_loop = False

	# Sleep for a bit
	time.sleep(SLEEP)