import csv
from langdetect import detect
## http[^\s]+[\n\r\s] to remove links


safe_tweets = []
with open('tweets_terrorism.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
    for row in spamreader:

        ## filter off empty tweets / tweets with < 6 chracters
        if len(row) == 0 or len(row[0]) <= 6:
            continue

        ## filter off non English tweets
        try:
            if detect(row[0]) == 'en':
                safe_tweets.append(row)
        except:
            print("This row throws and error:", row[0])

filename = "tweets_terrorism_cleaned.csv"

with open(filename, 'w') as csvfile: 
    csvwriter = csv.writer(csvfile)
    csvwriter.writerows(safe_tweets)