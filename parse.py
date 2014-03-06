"""
    This is a perser from .txt to JSON file
"""

import json

with open("filename.txt", "r") as f:
    with open("out.json", "w") as outfile:
        for tweet in f:

            date = tweet[7:tweet.find('",Author:')]
            author = tweet[tweet.find('",Author:"')+10:tweet.find('",Location:"')]
            location = tweet[tweet.find('",Location:"')+12:tweet.find('",Text:[')]
            text = tweet[tweet.find(',Text:[')+7:tweet.find('],Hashtags:[')]
            hashtags = tweet[tweet.find(',Hashtags:[')+11:tweet.find(']},')] 

            outfile.write(json.dumps({"Date" : date,
                       "Author": author,
                       "Location": location,
                       "Text": text,
                       "Hashtags" : hashtags}, indent=4))
            outfile.write(',')
            
outfile.close()
f.close()



