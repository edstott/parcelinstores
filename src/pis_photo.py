#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import os
import itertools
import subprocess

# Lamp to channel relationships
# Index is ordering (bulb is CHANNELS[-1])
CHANNELS = [12, 1, 25, 24, 23, 18]
N_LAMPS = len(CHANNELS)
PHOTO_PATH = 'imglib'

WEBCAM_SET = {'brightness':'128', 'contrast':'32', 'saturation':'32', \
	'white balance temperature, auto':'0', 'gain':'28', \
	'white balance temperature':'5132', 'sharpness':'72'}
WEBCAM_RES = '1920x1080'

fswebcam_args = ['-s '+setting+'='+value for setting,value in WEBCAM_SET.items()]
fswebcam_args += ['-r '+WEBCAM_RES,'--no-banner','--no-title']

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for lamp in CHANNELS:
	print 'Setting up lamp channel '+str(lamp)
	GPIO.setup(lamp, GPIO.OUT)
	GPIO.output(lamp, GPIO.LOW)

for lamp_cfg in itertools.product('01',repeat=N_LAMPS):
	print 'Lamp cfg '+''.join(lamp_cfg)
	for bulb in xrange(N_LAMPS):
		if lamp_cfg[bulb] == '0':
			GPIO.output(CHANNELS[bulb], GPIO.LOW)
			pass
		else:
			GPIO.output(CHANNELS[bulb], GPIO.HIGH)	
			pass
	
	time.sleep(0.5)	
	
	filename = os.path.join(PHOTO_PATH,''.join(lamp_cfg)+'.jpg')
	#print ' '.join(['fswebcam']+[filename]+fswebcam_args)
	subprocess.call(['fswebcam']+[filename]+fswebcam_args)

for channel in CHANNELS:
	print 'Closing lamp channel '+str(channel)
	pass
	GPIO.output(channel,GPIO.LOW)

GPIO.cleanup()

