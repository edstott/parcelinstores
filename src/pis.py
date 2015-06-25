#!/usr/bin/env python

import urllib2, ssl
from bs4 import BeautifulSoup
import time
from threading import Thread, Event
import random
from Queue import Queue
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

class StoppableThread(Thread):
	def __init__(self):
		super(StoppableThread, self).__init__()
		self._stop = Event()

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

class hardware(StoppableThread):
	def __init__(self, hardware_queue):
		Thread.__init__(self)

		self.hardware_queue = hardware_queue

		# Disable warnings for GPIO
		GPIO.setwarnings(False)

		# Dictionary to contain the flasher instances and randomised duty cycles for each channel
		self.pwms ={}

		# Setup the GPIO channels
		GPIO.setmode(GPIO.BCM)
		for channel in CHANNELS[:-1]:
			GPIO.setup(channel, GPIO.OUT)
			GPIO.output(channel, GPIO.LOW)

			flash_freq_rand = random.uniform(-FLASH_FREQ_RAND,FLASH_FREQ_RAND)
			flash_duty_rand = random.uniform(-FLASH_DUTY_RAND,FLASH_DUTY_RAND)

			self.pwms{channel} = (GPIO.PWM(pwmPin, FLASH_FREQ+flash_freq_rand), FLASH_DUTY+flash_duty_rand)

		self.start()

	def run(self):
		while not self.stopped():
			(channel, operation) = hardware_queue.get()
			# Bell channel - turn off and on quickly
			if channel is CHANNELS[-1]:
				GPIO.output(channel, GPIO.HIGH)
				time.sleep(0.025)
				GPIO.output(channel, GPIO.LOW)
				time.sleep(0.25)
				GPIO.output(channel, GPIO.HIGH)
				time.sleep(0.025)
				GPIO.output(channel, GPIO.LOW)
			# Other channels - start or stop the PWM
			else:
				if operation:
					self.pwms{channel}[0].start(self.pwms{channel}[1])
				else:
					self.pwms{channel}[0].stop()
			hardware_queue.task_done()
		# If the thread has been stopped, clean up the GPIO
		for channel in CHANNELS[:-1]:
			self.pwms{channel}[0].stop()
		GPIO.cleanup()

if __name__ == '__main__':

	try:
		# Hardware queue
		hardware_queue = Queue()
	
		# Fire up the hardware thread
		hardware = hardware(hardware_queue)
	
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
					time.sleep(5)
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
	
	

			# Loop through the new parcels and flash a blub for whoever has a parcel
			for person in CAS.keys():
				# If someone has a parcel
				if curr_parcels[person]:
					# Flash their bulb
					hardware_queue.put((CAS[person], True))
				# If they do have a flasher
				else:
					#But they don't have a parcel
					if not curr_parcels[person]:
						# Turn off their bulb
						hardware_queue.put((CAS[person], False))
	
			# Now loop through the data and see what has change - ring the bell for new parcels
			# Only do this after the first iteration of the loop
			try:
				for person in CAS.keys():
					new_parcels = [parcel for parcel in curr_parcels[person] if parcel not in prev_parcels[person]]
					# If there are any new parcels, ring the bell
					if new_parcels:
						# Ring the bell!
						hardware_queue.put((CHANNELS[-1], True))
						break
			# prev_parcels doesn't yet exist on first iteration
			except NameError:
				pass
	
			# Clean up before sleeping
			prev_parcels = curr_parcels.copy()	
			# Sleep for a bit
			time.sleep(SLEEP)
	
	except KeyboardInterrupt:
		hardware.stop()
		hardware.join()
