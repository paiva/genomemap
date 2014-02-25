import csv
import json

csvfile  = open('superbowl-2.csv', "r")
jsonfile  = open('out.json', "w")
fieldnames = ("Date", "Author", "Location", "Text", "Hashtags")

reader = csv.DictReader(csvfile,fieldnames)

for row in reader:

    json.dumps(row,jsonfile,indent=4)
    jsonfile.write('\n')

print(json.dumps(row,jsonfile,indent=4))

csvfile.close()
jsonfile.close()


