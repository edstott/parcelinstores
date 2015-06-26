#!/usr/bin/env python

import urllib2, ssl
from bs4 import BeautifulSoup
import time
import random
import RPi.GPIO as GPIO


# CAS members to watch and their bulb ordering
CAS = {'LEVINE,J':3, 'STOTT,E':5, 'DAVIS,J':1, 'OGDEN,P':4, 'HSISSEN,W':0, 'HUNG,E':2}

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
# Flashing period and random adjustment
FLASH_FREQ = 0.5
FLASH_FREQ_RAND= 0.1
FLASH_DUTY = 50
FLASH_DUTY_RAND = 10
# Stores website polling interval
SLEEP = 10
RETRY_SLEEP = 5

# Disable warnings for GPIO
GPIO.setwarnings(False)

# Dictionary to contain PWM instances and duty cycles for each person
pwms ={}

# Setup the GPIO channels
GPIO.setmode(GPIO.BCM)

# Setup the bulb channels
for person in CAS.keys():
	channel = CHANNELS[CAS[person]]

	GPIO.setup(channel, GPIO.OUT)
	GPIO.output(channel, GPIO.LOW)

	flash_freq_rand = random.uniform(-FLASH_FREQ_RAND,FLASH_FREQ_RAND)
	flash_duty_rand = random.uniform(-FLASH_DUTY_RAND,FLASH_DUTY_RAND)

	pwms[person] = (GPIO.PWM(channel, FLASH_FREQ+flash_freq_rand), FLASH_DUTY+flash_duty_rand)

# Setup the bell channel
	GPIO.setup(CHANNELS[-1], GPIO.OUT)
	GPIO.output(CHANNELS[-1], GPIO.LOW)

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

# Loop forever, sleeping between iterations
while True:
	# Open up the stores parcel tracker site, try again if times out
	response = None
	while response is None:
		try:
			response = urllib2.urlopen(STORES, timeout = 1)
			html = response.read()
		except urllib2.URLError, ssl.SSLError:
			time.sleep(RETRY_SLEEP)
			pass

	# Read the site and pass to BeautifulSoup
	soup = BeautifulSoup(html)

	# with open('ParcelTracking.html') as website:
	# 	html = website.read()
	# soup = BeautifulSoup(html)

	# Build current parcel data structure
	curr_parcels = {x:[] for x in CAS.keys()}

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
							curr_parcels[person].append(cells[0])

	ring_bell = False
	try:
		for person in CAS.keys():
			# Find parcels that weren't there before and now are - ring the bell if there are any
			if [parcel for parcel in curr_parcels[person] if parcel not in prev_parcels[person]]:
				ring_bell = True
			# Didn't previously have any parcels and now do - just delivered
			if not prev_parcels[person] and curr_parcels[person]:
				pwms[person][0].start(pwms[person][1])
			# Previously had parcels and now don't - just collected
			elif not curr_parcels[person] and prev_parcels[person]:
				pwms[person][0].stop()

	# On the first iteration prev_parcels doesn't exist
	except NameError:
		for person in CAS.keys():
			# Turn on the bulb for whoever has parcels
			if curr_parcels[person]:
				pwms[person][0].start(pwms[person][1])

	# Do the actual bell ringing if required
	if ring_bell:
		GPIO.output(channel, GPIO.HIGH)
		time.sleep(0.025)
		GPIO.output(channel, GPIO.LOW)
		time.sleep(0.25)
		GPIO.output(channel, GPIO.HIGH)
		time.sleep(0.025)
		GPIO.output(channel, GPIO.LOW)

	# Clean up before sleeping
	prev_parcels = curr_parcels.copy()
	# Sleep for a bit
	time.sleep(SLEEP)