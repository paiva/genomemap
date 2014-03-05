"""
Class that attaches to the Twitter Streaming API
"""
__author__ = 'Derek Ruths (druths@networkdynamics.org)'

#import requests
import json, sys

FILTER_URL = "https://stream.twitter.com/1/statuses/filter.json"
SAMPLE_URL = "https://stream.twitter.com/1/statuses/sample.json"

username= "stronnics" # should be a string
password = "S03752455666" # should be a string
tract_terms = [['#Oscars'],['#Oscars2014']]

TIMEOUT = 60*60*3

class TwitterStreamSampler:

	def __init__(self,username,password):
		"""
		Args
		----
			- ``username`` is a string containing the username of the authenticating account
			- ``password`` is a string containing the password of the authenticating account
		"""
		self.username = username
		self.password = password

	def start(self):
		r = requests.get(SAMPLE_URL, auth=(self.username,self.password))
		
		buf = ''
		for x in r.iter_content():
			buf += x
			if '\n' in buf:
				i = buf.index('\n')
				tweet = buf[:i]
				buf = buf[(i+1):]
				
				try:
					content = json.loads(tweet)
					print(tweet)
				except(Exception, e):
					print(e)
					sys.exit(1)

class TwitterStreamFilter:

	def __init__(self,username,password,track_terms):
		"""
		Args
		----
			- ``username`` is a string containing the username of the authenticating account
			- ``password`` is a string containing the password of the authenticating account
			- ``track_terms`` is a non-zero length list of lists of strings.  Each list of strings
			  specifies a set of terms that must all be found together (an AND operation). Each
			  list of strings is ORed together such that only one of the list of strings must be
			  satisfied for a tweet to pass the filter.
			
		For example, the constructor::
			
			TwitterStreamFilter('user','pass',[['happy 16th birthday'],['happy 18th birthday'],['happy 21st birthday']])
			
		creates a filter that will recognize happy birthday wishes for people turning 16, 18, and 21.
		"""
		self.username = username
		self.password = password
		self.track_terms = track_terms

	def start(self):
		track_string = ','.join([' '.join(x) for x in self.track_terms])
		r = requests.post(FILTER_URL, auth=(self.username,self.password), params={'track':track_string})
		
		buf = ''
		for x in r.iter_content():
			buf += x
			if '\n' in buf:
				i = buf.index('\n')
				tweet = buf[:i]
				buf = buf[(i+1):]
				
				try:
					content = json.loads(tweet)
					print(tweet)
				except(Exception,e):
					print(e)
					sys.exit(1)

if __name__ == '__main__':
	pass
