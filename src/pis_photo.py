#!/usr/bin/env python

#import RPi.GPIO as GPIO

# Lamp to channel relationships
# Index is ordering (bulb is CHANNELS[-1])
CHANNELS = [12, 1, 25, 24, 23, 18]
N_LAMPS = len(CHANNELS)

FRAG_X = 0
FRAG_Y = 0
FRAG_H = 128
FRAG_W = 1024

bulb_cfgs = {''.join(['0' for x in xrange(N_LAMPS)]):''}
img_frag = {}

photo_idx = 0
def takePhoto(filename):
	global photo_idx
	photoname = 'pis'+str(photo_idx)+'.jpg'
	#TAKE PHOTO
	photo_idx += 1
	return photoname
	
def cutPhoto(infile,outfile,lamp)
	fragpos = [FRAG_X,FRAG_Y+lamp*FRAG_H,FRAG_W]:
	pass

for lamp_cfg in xrange(2**N_LAMPS):
		bulb_cfg = '{0:'+str(N_LAMPS)+'b}'.format(lamp_cfg)
		for bulb in xrange(N_LAMPS):
			if bulb_cfg[bulb] = '0':
				#PIO.output(CHANNELS[bulb], GPIO.LOW)
				pass
			else:
				#GPIO.output(CHANNELS[bulb], GPIO.HIGH)	
				pass
				
		filename = bulb_cfg+'.jpg'
		#TAKE PHOTO
		
	
#Generate lamp configurations
for lamp in xrange(N_LAMPS):
	#print('lamp '+str(lamp))
	for adj_lamp in xrange(N_LAMPS):
		#print('lamp '+str(lamp)+' adj_lamp '+str(adj_lamp)+' lamp_sum '+str(lamp+adj_lamp))

		
		#Can we light bulb above?
		if lamp+adj_lamp < N_LAMPS:
			lamp_vector = ['0' for x in xrange(N_LAMPS)]
			lamp_vector[lamp+adj_lamp] = '1'
			bulb_cfg = ''.join(lamp_vector)
			
			#Take photo if not done already
			if bulb_cfg not in bulb_cfgs:	
					bulb_cfgs[bulb_cfg] = takePhoto()
					
			#Get image fragment
			fragname = 'l'+str(lamp)+'a'+str(adj_lamp)+'.jpg'
			cutPhoto(bulb_cfgs[bulb_cfg],fragname,lamp)
			img_frag
			
		
		#Can we light bulb below?
		if lamp-adj_lamp >= 0 and adj_lamp > 0:
			lamp_vector = ['0' for x in xrange(N_LAMPS)]
			lamp_vector[lamp-adj_lamp] = '1'
			bulb_cfg = ''.join(lamp_vector)
			
			#Take photo if not done already
			if bulb_cfg not in bulb_cfgs:	
					bulb_cfgs[bulb_cfg] = takePhoto()
					
			#Add image fragments
			#CUT_SEGMENT
			img_frag['l'+str(lamp)+'b'+str(adj_lamp)] = ''
		
		#Can we light both?
		if lamp-adj_lamp >= 0 and lamp+adj_lamp < N_LAMPS and adj_lamp > 0:
			lamp_vector = ['0' for x in xrange(N_LAMPS)]
			lamp_vector[lamp-adj_lamp] = '1'
			lamp_vector[lamp+adj_lamp] = '1'
			bulb_cfg = ''.join(lamp_vector)
			
			#Take photo if not done already
			if bulb_cfg not in bulb_cfgs:	
					bulb_cfgs[bulb_cfg] = takePhoto()
					
			#Add image fragments
			#CUT_SEGMENT
			img_frag['l'+str(lamp)+'ab'+str(adj_lamp)] = ''
		

#Take photos
photo_idx = 0		
for bulb_cfg in bulb_cfgs:
	for bulb in xrange(CHANNELS):
		if bulb_cfg[bulb] = '0':
			#PIO.output(CHANNELS[bulb], GPIO.LOW)
		else:
			#GPIO.output(CHANNELS[bulb], GPIO.HIGH)			

	
#Extract image fragments
for lamp in xrange(N_LAMPS):
	#print('lamp '+str(lamp))
	for adj_lamp in xrange(N_LAMPS):
	
print bulb_cfgs