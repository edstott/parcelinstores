#!/usr/bin/env python

import urllib2, ssl
from bs4 import BeautifulSoup
import time
import random
import RPi.GPIO as GPIO
import logging
import traceback
from datetime import datetime, timedelta
import cattTwitter

# CAS members to watch and their bulb ordering
# If initial equals first character of name, initial check is skipped
CAS = {'LEVINE,J':3, 'STOTT,S':5, 'DAVIS,J':1, 'OGDEN,P':4, 'HSISSEN,W':0, 'HUNG,E':2}

# Lamp to channel relationships
# Index is ordering (bulb is CHANNELS[-1])
CHANNELS = [12, 1, 25, 24, 23, 18, 14]
LEDS = [8,15]

# Credential file
LOGIN = '.credentials'
# Colour of new and collected parcels
NEW = {'bgcolor':'Beige'}
COLLECTED = {'bgcolor':'LightSteelBlue'}
# Flashing period and random adjustment
FLASH_FREQ = 0.5
FLASH_FREQ_RAND= 0.1
FLASH_DUTY = 50
FLASH_DUTY_RAND = 10

# Stores website polling interval
SLEEP = 60

#Log settings
LOG_FILE = "pis.log"
DEBUG_LEVEL = logging.INFO

#Stores settings
STORES = 'https://intranet.ee.ic.ac.uk/storesweb/parcels/GoodsInWeb.html'
STORES_DAYS = [1,2,3,4,5] #1 = Monday, 7 = Sunday
STORES_HOURS = ('08:30','17:00')
MAX_PARCEL_AGE = 4 #Maximum parcel age in days

#Twitter settings
TWITTER_EN = True
PIS_MSG = 'Parcel in Stores'

def checkparcels(CAS):
	# Open up the stores parcel tracker site, try again if times out
	html = None
	retry = 0
	while html is None:
		try:
			response = urllib2.urlopen(STORES, timeout = 1)
			html = response.read()
		except (urllib2.URLError, ssl.SSLError):
			retry_sleep = 2.0**retry
			retry += 1
			#logging.warning('Failed to read parcel tracker on attempt '+str(retry))
			#logging.warning('Retrying in '+str(retry_sleep)+' s')
			time.sleep(retry_sleep)

	if retry:
		logging.info('Connection restored on attempt '+str(retry+1))

	# Read the site and pass to BeautifulSoup
	soup = BeautifulSoup(html)

	#with open('ParcelTracking.html') as website:
	#	html = website.read()
	#soup = BeautifulSoup(html)

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
				# Date check
				age = (datetime.now() - datetime.strptime(cells[1],'%d/%m/%Y'))
				recent = age <= timedelta(MAX_PARCEL_AGE)
				for person in CAS.keys():
					(surname, initial) = person.split(',')
					# Check if the surname
					sNameMatch = any([True if name.upper().rstrip(',') == surname else False for name in cells[4].split(' ')])
					if sNameMatch:
						# Check the initial - only works if CAS members don't have same surname and forename initials!
						iNameMatch = any([True if name.upper()[0] == initial else False for name in cells[4].split(' ')])
						if recent and iNameMatch:
							curr_parcels[person].append(cells[0])
	return curr_parcels

#Setup logging
logging.basicConfig(filename=LOG_FILE,level=DEBUG_LEVEL,format='%(levelname)s %(asctime)s: %(message)s',datefmt='%a, %d %b %Y %H:%M:%S')
consolelog = logging.StreamHandler()
consolelog.setLevel(DEBUG_LEVEL)
consoleformatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s',datefmt='%a, %d %b %Y %H:%M:%S')
consolelog.setFormatter(consoleformatter)
logging.getLogger('').addHandler(consolelog)

logging.info('Starting parcelinstores')

#Setup opening hours
opentime = datetime.strptime(STORES_HOURS[0],'%H:%M').time()
closetime = datetime.strptime(STORES_HOURS[1],'%H:%M').time()
now = datetime.now()
storesopen = now.isoweekday() in STORES_DAYS and now.time()>opentime and now.time()<closetime
storeswasopen = storesopen

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

#Setup data
curr_parcels = checkparcels(CAS)
prev_parcels = curr_parcels.copy()

#Start twitter
if (TWITTER_EN):
	ctw = cattTwitter.cattTwitter()

# Catch exceptions from this point onwards so that GPIO can be reset
try:

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

		# Turn on all the PWMs but set their dutycycle to 0
		pwms[person][0].start(0)

		logging.info('Added parcel recipient '+person+' on channel '+str(CAS[person]))
	

	# Setup the bell channel
	GPIO.setup(CHANNELS[-1], GPIO.OUT)
	GPIO.output(CHANNELS[-1], GPIO.LOW)

	# Setup alive and status LEDs
	for LED in LEDS:
		GPIO.setup(LED,GPIO.OUT)
	aliveLED = GPIO.PWM(LEDS[0],2)
	aliveLED.start(0)
	statusLED = GPIO.PWM(LEDS[1],10)
	statusLED.start(0)

	# Turn on the bulb for whomever has parcels if starting when stores is open
	if storesopen:
		aliveLED.start(90)
		for person in CAS.keys():
			if curr_parcels[person]:
				pwms[person][0].ChangeDutyCycle(pwms[person][1])
	else:
		aliveLED.start(10)

	# Loop forever, sleeping between iterations
	logging.info('Commencing parcel monitor')
	while True:
		#Start status LED while processing
		statusLED.ChangeDutyCycle(50)

		#Is stores open
		now = datetime.now()
		storesopen = now.isoweekday() in STORES_DAYS and now.time()>opentime and now.time()<closetime

		ring_bell = False

		if storesopen:
			curr_parcels = checkparcels(CAS)
			for person in CAS.keys():
				# Find parcels that weren't there before and now are - ring the bell if there are any
				if [parcel for parcel in curr_parcels[person] if parcel not in prev_parcels[person]]:
					ring_bell = True
					logging.info('Parcel in stores for '+person)
				# Didn't previously have any parcels and now do - just delivered
				if not prev_parcels[person] and curr_parcels[person]:
					pwms[person][0].ChangeDutyCycle(pwms[person][1])
				# Previously had parcels and now don't - just collected
				elif not curr_parcels[person] and prev_parcels[person]:
					pwms[person][0].ChangeDutyCycle(0)
					logging.info(person + ' collected their parcel(s)')
		
		# Turn on the bulb for whomever has parcels when stores open
		if storesopen and not storeswasopen: 
			logging.info('Stores has opened')
			aliveLED.ChangeDutyCycle(90)				
			for person in CAS.keys():
				if curr_parcels[person]:
					pwms[person][0].ChangeDutyCycle(pwms[person][1])
 		# Turn off bulbs when stores closes
		if not storesopen and storeswasopen:
			logging.info('Stores has closed')
			aliveLED.ChangeDutyCycle(10)	
			for person in CAS.keys():
				pwms[person][0].ChangeDutyCycle(0)		

		# Do the actual bell ringing if required
		if ring_bell:
			GPIO.output(CHANNELS[-1], GPIO.HIGH)
			time.sleep(0.025)
			GPIO.output(CHANNELS[-1], GPIO.LOW)
			time.sleep(0.25)
			GPIO.output(CHANNELS[-1], GPIO.HIGH)
			time.sleep(0.025)
			GPIO.output(CHANNELS[-1], GPIO.LOW)

			if (TWITTER_EN):
				lamp_pattern = [''] * len(CAS)
				for person,bulb in CAS:
					lamp_pattern[bulb] = '1' if curr_parcels[person] else '0'				
				imagefile=os.path.join('imglib',''.join(lamp_pattern)+'.gif')
				ctw.tweetqueue.put(cattTwitter.cattTweet(PIS_MSG,image=imagefile))
				logging.info('Sent tweet')

		# Clean up before sleeping
		prev_parcels = curr_parcels.copy()
		storeswasopen = storesopen

		#Stop status LED when finished
		statusLED.ChangeDutyCycle(0)

		# Sleep for a bit
		time.sleep(SLEEP)
except KeyboardInterrupt:
	logging.info('Exit due to SIGINT')
	aliveLED.stop()
	for pwm in pwms:
		pwms[pwm][0].stop()
	
	for channel in CHANNELS:
		GPIO.output(channel,GPIO.LOW)

	GPIO.cleanup()
	if TWITTER_EN:
		ctw.kill()

except:
	logging.error('Exception: shutting down GPIO')
	with open('pis.error','w') as errlog:
		traceback.print_exc(None,errlog)
	GPIO.cleanup()
	raise
