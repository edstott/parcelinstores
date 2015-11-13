#!/usr/bin/env python

#import RPi.GPIO as GPIO

# Lamp to channel relationships
# Index is ordering (bulb is CHANNELS[-1])
CHANNELS = [12, 1, 25, 24, 23, 18]
N_LAMPS = len(CHANNELS)
PHOTO_PATH = imglib

for lamp_cfg in xrange(2**N_LAMPS):
		bulb_cfg = '{0:'+str(N_LAMPS)+'b}'.format(lamp_cfg)
		for bulb in xrange(N_LAMPS):
			if bulb_cfg[bulb] = '0':
				#GPIO.output(CHANNELS[bulb], GPIO.LOW)
				pass
			else:
				#GPIO.output(CHANNELS[bulb], GPIO.HIGH)	
				pass
				
		filename = os.path.join(PHOTO_PATH,bulb_cfg+'.jpg')
		#TAKE PHOTO
