#!/usr/bin/env python

import urllib2, ssl
from bs4 import BeautifulSoup
import time
from threading import Thread, Event
import random


# CAS members to watch and their bulb ordering
CAS = {'LEVINE,J':3, 'STOTT,E':5, 'DAVIS,J':1, 'OGDEN,P':4, 'WIJEYASINGHE,M':0, 'HUNG,E':2}
# Build current and new dictionaries
cas_prev = {x:[] for x in CAS.keys()}
cas_new = {x:[] for x in CAS.keys()}

# Lamp to channel relationships
# Index is ordering (bulb is CHANNELS[-1])
CHANNELS = [12, 1, 25, 24, 23, 18, 14]

# Credential file
LOGIN = '.credentials'
# URL of stores parcel tracker
STORES = 'https://intranet.ee.ic.ac.uk/storesweb/parcels/GoodsInWeb.html'
# Colour of new and collected parcels
NEW = {'bgcolor':'Beige'}
COLLECTED = {'bgcolor':'LightSteelBlue'}
FLASH = 1.0
FLASH_RANDOM = 0.25

class StoppableThread(Thread):
	def __init__(self):
		super(StoppableThread, self).__init__()
		self._stop = Event()

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()


class flasher(StoppableThread):
	def __init__ (self, channel, flash_queue):

		Thread.__init__(self)

		self.channel = channel
		self.flash_queue = flash_queue

		# Randomised on and off periods for that vintage feel
		self.on_time = FLASH + random.uniform(-FLASH_RANDOM,FLASH_RANDOM)
		self.off_time = FLASH +  random.uniform(-FLASH_RANDOM,FLASH_RANDOM)

		# Start the flasher thread
		self.start()

	def run(self):
		status = True
		while not stopped():
			self.flash_queue.put((self.channel, True))
			self._stop.wait(self.on_time)
			self.flash_queue.put((self.channel, False))
			self._stop.wait(self.off_time)

if __name__ is '__main__':
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
					for person in CAS.keys():
						(surname, initial) = person.split(',')
						# Check if the surname
						if any([True if name.upper() == surname else False for name in cells[4].split(' ')]):
							# Check the initial - only works if CAS members don't have same surname and forename initials!
							if any([True if name.upper()[0] == initial else False for name in cells[4].split(' ')]):
								cas_new[person].append(cells[0])


		# Loop through the new parcels and fire up flashers for each person who has a parcel
		for person in CAS.keys():
			if not cas_new[person]:


		# Now loop through the data and see what has change - ring the bell for new parcels
		# Only do this after the first iteration of the loop
		if not first_loop:
			for person in CAS.keys():
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