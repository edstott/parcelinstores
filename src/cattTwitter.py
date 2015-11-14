import twitter
import os
import time
import Queue
import logging
import threading
import urllib2

TWITTER_CREDS = os.path.expanduser('~/.catt_credentials')
CONSUMER_KEY = "eRENCvbmZ1mfSSyis9uVMstGb"
CONSUMER_SECRET = "meWNE4ndZ33LNCarMUnwhI1OKZU06c1HdsfxGKzihaAoffWga1"

class cattTweet:

	def __init__(self,text,**kwargs):
		self.text = text
		if 'image' in kwargs:
			self.image = kwargs['image']
		else:
			self.image = None
		

class cattTwitter:

	def __init__(self):
		self.twitterthread = threading.Thread(target=tweeter,args=[self])
		self.tweetqueue = Queue.Queue(0)
		self.twitterthread.daemon = True
		self.twitterthread.start()

	def kill(self):
		logging.debug('Killing Twitter thread')
		self.tweetqueue.put(None)
		#logging.debug('Waiting for Twitter thread')
		#self.twitterthread.join()

def tweeter(ctw):

	if not os.path.exists(TWITTER_CREDS):
		twitter.oauth_dance("Catt", CONSUMER_KEY,CONSUMER_SECRET,TWITTER_CREDS)

	oauth_token, oauth_secret = twitter.read_token_file(TWITTER_CREDS)
	tw = twitter.Twitter(auth=twitter.OAuth(oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET))

	logging.info('Started Twitter')

	while (True):
		newtweet = ctw.tweetqueue.get()
		if newtweet == None: #Placing None on tweet queue kills the thread
			logging.debug('Twitter thread received kill command')
			break
		else:
			attempt = 1
			while not tweet(newtweet,tw):
				retryint = 2.0**(attempt-1)
				logging.warning('Tweet failed. Attempt %d. Retry in %f s',attempt,retryint)
				attempt += 1
				time.sleep(retryint)
			

def tweet(newtweet,tw):
	try:
		if newtweet.image == None:
			tw.statuses.update(status=newtweet.text)
			logging.info('Tweeted \"%s\"',newtweet.text)
		else:
			with open(newtweet.image,"rb") as imagefile:
				tparams = {"media[]":imagefile.read(),"status":newtweet.text}
			tw.statuses.update_with_media(**tparams)
			logging.info('Tweeted \"%s\" with photo %s',newtweet.text,newtweet.image)
	except urllib2.URLError:
		return False
	else:
		return True

