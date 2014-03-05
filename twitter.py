"""
This module provides programmatic access to the Twitter REST API.
"""
__author__ = 'Network Dynamics Lab, McGill University'

import json, urllib
import logging
import oauth2 as oauth
import types
import time
import random
import datetime
import os, os.path

logger = logging.getLogger('roost.spider.twitter')

__all__ = ['TwitterAPI']

user_timeline_url = 'http://api.twitter.com/1/statuses/user_timeline.json'
friends_url = 'http://api.twitter.com/1/friends/ids.json'
followers_url = 'http://api.twitter.com/1/followers/ids.json'
profile_url = 'http://api.twitter.com/1/users/show.json'
rate_limit_url = 'http://api.twitter.com/1/account/rate_limit_status.json'
tweet_url = 'http://api.twitter.com/1/statuses/show.json'
home_timeline_url = 'http://api.twitter.com/1/statuses/home_timeline.json'

SUCCESS_RESP = '200'
NOT_MODIFIED_RESP = '304'
BAD_REQUEST_RESP = '400'
UNAUTHORIZED_RESP = '401'
FORBIDDEN_RESP = '403'
NOT_FOUND_RESP = '404'
NOT_ACCEPTABLE_RESP = '406'
ENHANCE_CALM_RESP = '420'
INTERNAL_SERVER_ERROR_RESP = '500'
BAD_GATEWAY_RESP = '502'
SERVICE_UNAVAILABLE_RESP = '503'

# These can be filled in with your oauth information for Twitter
# rather than using the file-based setup. Copy each component
# into here as a string.
#
# Note that this is the least secure way of doing this since
# you're putting authentication information into a file that could easily
# be shared with others.
CONSUMER_KEY = 'n66rh4MZzp0PJrrNQKbDw' 	# 'asdfasdfasdf'
SECRET_KEY = 'XtjY7kJO4Qq8UthbdfqmY5F2P3uDA3zwh4t6usjYcaI' 		# 'asdfasdfasdf'
OTOKEN = '201313019-nY8HaaVVlr5ZEVczXGURfDRXB62CMPKeQz3pzK5t'			# 'asdfasdfasdf'
OTOKEN_SECRET = 'tTliPJHUPeRaaESkoR9oazPe743qCheL1qMsxw35mi91t'	# 'asdfasdfasdf'

class FatalTwitterResponse(RuntimeError):
	def __init__(self,resp_code,description,response,content):
		RuntimeError.__init__(self,'response code: %s, description: %s, response: %s, content: %s' % (resp_code, description, response,content))
		
		self._code = resp_code
		self._description = description
		self._resp = response
		self._content = content
		
	def code(self):
		return self._code

	def description(self):
		return self._description

	def response(self):
		return self._resp
		
	def content(self):
		return self._content

class TwitterAPI:
	
	def __init__(self, **kwargs):
		"""
		A TwitterAPI object can be initialized in three ways.  
		
		  1) The profile keyword: the roost profile name which corresponds 
				to a .oauth profile in the ${HOME}/.roost directory can be
				given. E.g.
				
					TwitterAPI(profile='jdoe')
					
				There must be a file ${HOME}/.roost/jdoe.profile which contains a
				JSON dictionary specifying the consumer_key, secret_key, otoken, and otoken_secret (all strings).
				
		  2) The profile_file keyword: a complete path to and including the
				filename of the profile to use.
				
		  3) The consumer_key, secret_key, otoken, and otoken_secret keywords: in this case, the caller is
				explicitly indicating the keys and tokens that will be used for authentication with Twitter.
				
		Other (optional) keywords:
			
		  - capacity_wait_time [default 60] is the number of seconds to make the next call to Twitter wait if the servers
				report being over capacity.
		"""
		
	def __init__(self, **kwargs):
		
		global_details_specified = CONSUMER_KEY != None or SECRET_KEY != None or OTOKEN != None or OTOKEN_SECRET != None
		kw_details_specified = 'consumer_key' in kwargs or 'secret_key' in kwargs or 'otoken' in kwargs or 'otoken_secret' in kwargs
		
		details_specified = kw_details_specified or global_details_specified
		
		consumer_key = kwargs.pop('consumer_key',CONSUMER_KEY)
		secret_key = kwargs.pop('secret_key',SECRET_KEY)
		otoken = kwargs.pop('otoken',OTOKEN)
 		otoken_secret = kwargs.pop('otoken_secret',OTOKEN_SECRET)
		
		if details_specified:
			logger.debug('detailed oauth info specified:\n\tconsumer_key = %s\n\tsecret_key = %s\n\totoken = %s\n\totoken_secret = %s' %
							(consumer_key,secret_key,otoken,otoken_secret))
		else:			
			if 'profile' not in kwargs and 'profile_file' not in kwargs:
				kwargs['profile'] = 'default'
		
		if 'profile' in kwargs:
			if details_specified:
				raise Exception, 'the profile keyword cannot be specified alongside the explicit oauth detail keywords'
			elif 'profile_file' in kwargs:
				raise Exception, 'the profile keyword cannot be used alongside the profile_file keyword'
			
			fname = os.path.join(os.environ['HOME'],'.roost','%s.profile' % kwargs.pop('profile'))
			logger.debug('loading oauth info from profile file %s' % fname)
			consumer_key, secret_key, otoken, otoken_secret = self.read_profile_oauth_info(fname)
		elif 'profile_file' in kwargs:
			if details_specified:
				raise Exception, 'the profile keyword cannot be specified alongside the explicit oauth detail keywords'
			elif 'profile' in kwargs:
				raise Exception, 'the profile_file keyword cannot be used alongside the profile keyword'
				
			logger.debug('loading oauth info from profile file %s' % kwargs['profile_file'])
			fname = kwargs.pop('profile_file')
			consumer_key, secret_key, otoken, otoken_secret = self.read_profile_oauth_info(fname)

		logger.debug('oauth info:\n\tconsumer_key = %s\n\tsecret_key = %s\n\totoken = %s\n\totoken_secret = %s' %
						(consumer_key,secret_key,otoken,otoken_secret))

		if consumer_key == None:
			raise Exception, 'a value for consumer_key was not specified'
		elif secret_key == None:
			raise Exception, 'a value for secret_key was not specified'
		elif otoken == None:
			raise Exception, 'a value for otoken was not specified'
		elif otoken_secret == None:
			raise Exception, 'a value for otoken_secret was not specified'
							
		# handle other optional arguments
		self._capacity_wait_time = kwargs.pop('capacity_wait_time',60)
		
		# any other dangling arguments?
		if len(kwargs):
			raise Exception, 'Unknown arguments: %s' % ', '.join(kwargs.keys())
		
		# done reading - build the TwitterAPI object
		self._consumer_info = { 'key':consumer_key, 'secret_key':secret_key }
		self._otoken_info = { 'token':otoken, 'secret':otoken_secret }
		
		self._capacity_resume_time = 0
		
		self._max_wait_interval = 10
		
		self._num_remote_calls = 0
		
		rate_limit = self.get_rate_limit()
		self._rate_limit = int(rate_limit['hourly_limit'])
		self._rate_limit_remaining = int(rate_limit['remaining_hits'])
		self._rate_limit_reset = int(rate_limit['reset_time_in_seconds'])
	
	def read_profile_oauth_info(self,fname):
		fh = open(fname,'r')
		data = json.load(fh)
		
		return data['consumer_key'], data['secret_key'], data['otoken'], data['otoken_secret']
		
	def get_json(self, url, params):
		
		# if twitter is over capacity
		curr_time = time.time()
		if self._capacity_resume_time > curr_time:
			delta = int(self._capacity_resume_time - curr_time + random.randint(1,self._max_wait_interval))
			logger.warn('twitter is over capacity, sleeping for %d sec (@ %s)' % (delta,str(datetime.datetime.now())))
			time.sleep(delta)
			curr_time = time.time()
		
		# if we've hit the rate limit, wait
		if url != rate_limit_url and self._rate_limit_remaining == 0 and self._rate_limit_reset > curr_time:
			delta = int(self._rate_limit_reset - curr_time + random.randint(1,self._max_wait_interval))
			logger.warn('hit rate limit, sleeping for %d sec (@ %s)' % (delta,str(datetime.datetime.now())))
			time.sleep(delta)
		
		consumer = oauth.Consumer(key=self._consumer_info['key'],secret=self._consumer_info['secret_key'])
		token = oauth.Token(self._otoken_info['token'], self._otoken_info['secret'])
		client = oauth.Client(consumer, token)
		
		self._num_remote_calls += 1
		resp, content = client.request(url + "?" + urllib.urlencode(params), "GET")
		retry = False
		missing_info = False
		
		# update the rate limit status
		if url != rate_limit_url and 'x-ratelimit-limit' in resp:
			self._rate_limit = int(resp['x-ratelimit-limit'])
			self._rate_limit_remaining = int(resp['x-ratelimit-remaining'])
			self._rate_limit_reset = int(resp['x-ratelimit-reset'])
		
		# handle the result
		if resp['status'] == NOT_MODIFIED_RESP:
			logger.warn('twitter returned no data')
			missing_info = True
		if resp['status'] == BAD_GATEWAY_RESP or resp['status'] == SERVICE_UNAVAILABLE_RESP:
			logger.warn('twitter reported over capacity')
			self._capacity_resume_time = time.time() + self._capacity_wait_time
			retry = True
		elif resp['status'] == INTERNAL_SERVER_ERROR_RESP:
			#raise FatalTwitterResponse(INTERNAL_SERVER_ERROR_RESP, 'Something is broken on Twitter', resp, content)
			logger.warn('twitter reported an internal server error on %s, %s' % (url,str(params)))
			retry = True
		elif resp['status'] == BAD_REQUEST_RESP or resp['status'] == ENHANCE_CALM_RESP:
			logger.warn('twitter reported exceeded rate limit')
			# we need to rate limit
			retry = True
		elif resp['status'] == NOT_ACCEPTABLE_RESP:
			raise FatalTwitterResponse(resp['status'], 'No idea what happened', resp, content)
		elif resp['status'] == NOT_FOUND_RESP or resp['status'] == UNAUTHORIZED_RESP or resp['status'] == FORBIDDEN_RESP:
			missing_info = True
		# if not content was returned, but the response was successful, this usually means that the message is missing
		if resp['status'] == SUCCESS_RESP and len(content) == 0:
			missing_info = True
		
		return retry, missing_info, resp, content

	def get_rate_limit(self):
		retry, missing_info, resp, content = self.get_json(rate_limit_url, {})
		return json.loads(content)

	def get_followers(self,user_id):
		"""
		Returns a list of the user's followers.  If the user's account was unavailable 
		(either due to authorization or existence issues), then None is returned.
		"""
		cursor = -1
		thelist = []
		stillAvailable = True
		missing_info = False
		while stillAvailable:
			neighbors = None
			if type(user_id) == str:
				retry, missing_info, resp, content = self.get_json(followers_url, {"screen_name": user_id, "cursor" : cursor})
			else:
				retry, missing_info, resp, content = self.get_json(followers_url, {"user_id": user_id, "cursor" : cursor})
			
			if retry:
				continue
			
			if missing_info:
				return None
			
			neighbors = json.loads(content)
			
			if 'ids' in neighbors:
				for user in neighbors['ids']:
					thelist.append(user)
				cursor = neighbors['next_cursor']
				stillAvailable = True if cursor > 0 else False
			else:
				stillAvailable = False
		return thelist

	def get_friends(self,user_id):
		"""
		Returns a list of the user's friends.  If the user's account was unavailable 
		(either due to authorization or existence issues), then None is returned.
		"""
		cursor = -1
		thelist = []
		stillAvailable = True
		while stillAvailable:
			neighbors = None
			if type(user_id) == str:
				retry, missing_info, resp, content = self.get_json(friends_url, {"screen_name": user_id, "cursor" : cursor})
			else:
				retry, missing_info, resp, content = self.get_json(friends_url, {"user_id": user_id, "cursor" : cursor})
				
			if retry:
				continue
			
			if missing_info:
				return None
					
			neighbors = json.loads(content)
				
			if 'ids' in neighbors:
				for user in neighbors['ids']:
					thelist.append(user)
				cursor = neighbors['next_cursor']
				stillAvailable = True if cursor > 0 else False
			else:
				stillAvailable = False
		return thelist

	def get_profile(self,user_id):
		"""
		Returns a user's profile.  If the user's account was unavailable 
		(either due to authorization or existence issues), then None is returned.
		"""
		cursor = -1
		thelist = []
		retry = True
		
		profile = None
		content = None
		while retry:
			if type(user_id) == str:
				retry, missing_info, resp, content = self.get_json(profile_url, {"screen_name": user_id})
			else:
				retry, missing_info, resp, content = self.get_json(profile_url, {"user_id": user_id})
		
		if missing_info:
			return None
		
		profile = json.loads(content)
		
		return profile

	def get_tweets(self,user_id,num_tweets=1000,**kwargs):
		"""
		Returns a list of the user's tweets.  If the user's account was unavailable 
		(either due to authorization or existence issues), then None is returned.
		"""
		
		# add defaults
		if 'include_rts' not in kwargs:
			kwargs['include_rts'] = 1
		if 'trim_user' not in kwargs:
			kwargs['trim_user']= 1
		
		tweets = []
		stats = {'num_remote_calls':0}

		# resp, userdata = self.get_json(user_timeline_url, {"user_id": user_id, "count" : 200, "page" : p}, jsonvalue=False)
		# if resp['status'] == '401':
		# 	logging.info("user %s was not available" % user_id)
		# 	return None
	
		# collect all of a user's tweets
		max_id = None
		while True:
			logger.debug('requesting tweets for user %s, max_id %d, %d tweets collected (num_remote_calls %d)' % (str(user_id),-1 if max_id is None else max_id,len(tweets),self._num_remote_calls))
			
			resp = None
			userdata = None
			if type(user_id) == str:
				stats['num_remote_calls'] += 1
				params = {"screen_name":user_id, "count":200} # , "trim_user":1, "include_rts":1
				params.update(kwargs)
				if max_id != None:
					params['max_id'] = max_id - 1
				retry, missing_info, resp, userdata = self.get_json(user_timeline_url, params)
			else:
				stats['num_remote_calls'] += 1
				params = {"user_id":user_id, "count":200} # , "trim_user":1, "include_rts":1
				params.update(kwargs)
				if max_id != None:
					params['max_id'] = max_id - 1
				retry, missing_info, resp, userdata = self.get_json(user_timeline_url, params)
			
			if missing_info:
				return None
			
			if retry:
				logger.info("need to retry getting tweets for user %s" % str(user_id))
			elif resp['status'] == '200':
				userdata = json.loads(userdata)
				
				# if there's no tweet data, just stop
				# TODO: Does this need to be here any more now that we're checking for missing info in the JSON call?
				if len(userdata) == 0:
					break
					
				for status in userdata:
					# update the max_id
					if status['id'] < max_id:
						max_id = status['id']
						
					tweets.append(status)
					
					if len(tweets) >= num_tweets:
						break
						
			else:
				logger.debug('unknown result with status code %s for user id %s' % (resp['status'],str(user_id)))
				pass

			if len(tweets) >= num_tweets:
				break

		logger.debug('finished collecting tweets for user %s. Stats: %s' % (str(user_id),str(stats)))

		return tweets

	def get_tweet(self,tweet_id,**kwargs):
		"""
		Returns a specific tweet.  If the user's account was unavailable 
		(either due to authorization or existence issues), then None is returned.
		"""
		retry = True

		profile = None
		content = None
		while retry:
			params = {"id": int(tweet_id)}
			params.update(kwargs)
			retry, missing_info, resp, content = self.get_json(tweet_url, params)

			if missing_info:
				return None
				
		tweet = json.loads(content)

		return tweet
		
if __name__ == '__main__':
	import sys
	import argparse
	
	def get_user_identifier(x):
		try:
			return int(x)
		except ValueError:
			return x
	
	parser = argparse.ArgumentParser(description='A utility for interacting with Twitter')
	parser.add_argument('--debug','-d',choices=['DEBUG','INFO','WARN','ERROR','FATAL'],default='ERROR',help='set the logging level')
	parser.add_argument('--profile','-P',help='set the Twitter profile that will be used')
	parser.add_argument('command',help='the twitter command to perform')
	parser.add_argument('args',metavar='A',nargs='*',help='arguments for the twitter command')
	
	args = parser.parse_args()
	
	# setup debugging
	eval('logging.basicConfig(level=logging.%s)' % args.debug)
	
	# use the profile to get the Twitter API access
	if args.profile is None:
		api = TwitterAPI()
	else:
		api = TwitterAPI(profile=args.profile)
	
	if args.command == 'rlimit':
		rate_limit = api.get_rate_limit()
		max_len = max([len(k) for k in rate_limit])
		for k,v in rate_limit.items():
			print '  %s%s' % ((str(k) + ':').ljust(max_len+2),str(v))
	elif args.command == 'followers':
		screen_name = get_user_identifier(args.args[0])
		followers = api.get_followers(screen_name)
		print '\n'.join(map(str,followers))
	elif args.command == 'friends':
		screen_name = get_user_identifier(args.args[0])
		friends = api.get_friends(screen_name)
		print '\n'.join(map(str,friends))	
	elif args.command.startswith('user_tweets'):
		screen_name = get_user_identifier(args.args[0])
		num_tweets = 10
		if len(args.args) > 1:
			num_tweets = int(args.args[1])
		tweets = api.get_tweets(screen_name,num_tweets=num_tweets)
		
		for tweet in tweets:
			if args.command == 'user_tweets_text':
				print tweet['text']
			elif args.command == 'user_tweets':
				print tweet
			else:
				print 'Unknown command: ',args.command
				quit()
				
	elif args.command == 'user_created_at':
		screen_name = get_user_identifier(args.args[0])
		info = api.get_profile(screen_name)
		print info['created_at']
	elif args.command == 'profile':
		screen_name = get_user_identifier(args.args[0])
		info = api.get_profile(screen_name)
		max_len = max([len(k) for k in info])
		info = info.items()		
		info.sort(cmp=lambda x,y: cmp(x[0],y[0]))
		
		for k,v in info:
			print '%s %s' % ((k + ':').ljust(max_len+2),str(v))
			
	elif args.command == 'home_text':
		screen_name = get_user_identifier(args.args[0])
		tweets = api.get_home_timeline(screen_name,num_tweets=10)
		for tweet in tweets:
			print tweet['text']
	elif args.command.startswith('tweet'):
		tweet_id = long(args.args[0])
		tweet = api.get_tweet(tweet_id,include_entities=True)
		
		if args.command == 'tweet':
			print tweet
		elif args.command == 'tweet_text':
			print tweet['text']
		else:
			print 'Unknown command: ',args.command
			quit()
	else:
		print 'Unknown command: ',args.command
