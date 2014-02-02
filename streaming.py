from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

access_token_key = "201313019-NBXXI5i97Kd0Efr9gwY3xCVV6c2xwbBS7VYu6P1a"
access_token_secret = "w8LUQIqckxqbcdjb9L2E0OJ00aHD4ZVQogc6bGkJls46M"

consumer_key = "TwhZ4ZDN6akZfa4eek5A"
consumer_secret = "INSkPv6WJuADNTs1hv7D6REH8f0K9F07aSDxrgf1hw"

class listener(StreamListener):

	def on_data(self,data):
		print data
		return True

	def on_error(self,status):
		print status

auth = OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token_key,access_token_secret)
twitterStream = Stream(auth, listener())
twitterStream.filer(track=["SuperBowl"])
