import json

positive_keys = ['yes', '#yes', 'Yes', '#Yes','YES','#YES','Thank', '#Thank'
                 'THANK','thank','Thanks','#THANK','#thank','#Thanks','thanks', '#thanks',
                 'THANKS', '#THANKS', 'good', '#good', 'Good', '#Good' , 'GOOD','#GOOD']

negative_keys = ['No', '#No' , 'NO', 'no', 'Why', 'WHY', 'why', 'bad', 'Bad', 'BAD', 'lame',
                 '#NO', '#no', '#Why', '#WHY', '#why', '#bad', '#Bad', '#BAD', '#lame']

positive_tweets = 0
negative_tweets = 0


def sentiment(text,keys):
    for word in text.split():
          for key in keys:
                if(word == key):
                    return True
                
with open("flappybird.json") as json_file:
    tweets = json.load(json_file)

    for i in range(0,len(tweets)):
        text = tweets[i]['Text']
        if(sentiment(text,positive_keys)):
            positive_tweets = positive_tweets + 1
                    
        elif(sentiment(text,negative_keys)):
            negative_tweets = negative_tweets +1
            
print("Positive tweets: ", positive_tweets)
print("Negative tweets: ", negative_tweets)

