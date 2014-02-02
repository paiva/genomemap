from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

access_token_key = "201313019-NBXXI5i97Kd0Efr9gwY3xCVV6c2xwbBS7VYu6P1a"
access_token_secret = "w8LUQIqckxqbcdjb9L2E0OJ00aHD4ZVQogc6bGkJls46M"
consumer_key = "TwhZ4ZDN6akZfa4eek5A"
consumer_secret = "INSkPv6WJuADNTs1hv7D6REH8f0K9F07aSDxrgf1hw"
username = "stronnics"
password = "S03752455666"

class listener(StreamListener):

    def on_data(self, data):
	try:
        	#print data

		tweet = data.split(',"text":"')[1].split('","source')[0]
		
		# Using ":::" to separate time and tweets
		saveThis = str(time.time() + ":::" + tweet)
		saveFile = open("twitDB2.csv", "a")
		saveFile.write(saveThis)
		saveFile.write("\n")
		saveFile.close()
        	return True
	except BaseException, e:
		print "faile on data", str(e)
		time.sleep(5)


    def on_error(self, status):
        print status

auth = OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token_key,access_token_secret)

# Works with basic authentication, refuses auth
twitterStream = Stream(username,password, listener())
twitterStream.filter(track=["SuperBowl"])


