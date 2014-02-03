from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

access_token_key = "Insert code here"
access_token_secret = "Insert code here"
consumer_key = "Insert code here"
consumer_secret = "Insert code here"
username = "Insert username"
password = "Insert password"

class listener(StreamListener):

    def on_data(self, data):
        try:
        	
            text = data.split(',"text":"')[1].split('","source')[0]
            location = data.split(',"location":"')[1].split('","url')[0]
            date = data.split('{"created_at":"')[1].split('","id')[0]
            author = data.split(',"screen_name":"')[1].split('","location"')[0]
            hashtags = data.split('"hashtags":[')[1].split('],"symbols')[0]   

	    # Tweet composed of date, author, location, text, and hashtags. 	
            saveThis = str("{" + "Date:" + '"' + date + '",' + "Author:" + '"@' + author + '",' + "Location:" + '"' + location + '",'+ "Text:" + '[' + text + '],' + "Hashtags:" + "[" + hashtags + "]" + "},")
 	
	    # Saves into a CVS file named "tweeter"	 	
            saveFile = open("tweeter.csv", "a")
            saveFile.write(saveThis)
            saveFile.write("\n")
            saveFile.close()
            return True
        
        except BaseException, e:
            print "failed on data", str(e)
            time.sleep(5)


    def on_error(self, status):
        print status

auth = OAuthHandler(consumer_key,consumer_secret)
auth.set_access_token(access_token_key,access_token_secret)

#If script refuses auth authentication, use basic authentication instead (username and password)
#twitterStream = Stream(username,password, listener())
twitterStream = Stream(auth, listener())
twitterStream.filter(track=["SuperBowl,Super Bowl"])
