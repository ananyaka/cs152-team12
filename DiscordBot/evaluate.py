import openai
from datasets import load_dataset
import dsp
import csv
from string import punctuation, whitespace
import os
import json
import numpy as np


terrorism_data = []
with open("tweets_terrorism_cleaned.csv") as csvfile:
    spamreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
    for row in spamreader:
        try:
            ## a lot of terrorism tweets have leading/trailing punctuations / whitespaces
            stripped_sentence = row[0].strip(punctuation + whitespace)
            terrorism_data.append(stripped_sentence)
        except:
            continue

# print(len(terrorism_data), terrorism_data[0])
terrorism_data = np.random.choice(terrorism_data, size=8000, replace=False)

safe_data = []
with open("tweets_safe_cleaned.csv") as csvfile:
    spamreader = csv.reader(csvfile, delimiter='\t', quotechar='|')
    for row in spamreader:
        try:
            stripped_sentence = row[0].strip(punctuation + whitespace)
            safe_data.append(stripped_sentence)
        except:
            continue

# print(len(safe_data), safe_data[0])
safe_data = np.random.choice(safe_data, size=8000, replace=False)


# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    openai.organization = tokens['openai_organization']
    openai.api_key = tokens['openai_api_key']


def classify(message, terrorism_examples, safe_examples):

    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
    {"role": "system", "content": "You are a content moderation system. Classify each input as either terrorism or safe."},
    {"role": "user", "content": terrorism_examples[0]},
    {"role": "assistant", "content": "terrorism"},
    {"role": "user", "content": safe_examples[0]},
    {"role": "assistant", "content": "safe"},
    {"role": "user", "content": terrorism_examples[1]},
    {"role": "assistant", "content": "terrorism"},
    {"role": "user", "content": safe_examples[1]},
    {"role": "assistant", "content": "safe"},
    {"role": "user", "content": terrorism_examples[2]},
    {"role": "assistant", "content": "terrorism"},
    {"role": "user", "content": safe_examples[2]},
    {"role": "assistant", "content": "safe"},
    {"role": "user", "content": message}
    ]
    )

    output = response['choices'][0]['message']['content']
    return output


def evaluate(terrorism_data, safe_data, percentage_test = 0.001, num_example = 6):
    terrorism_cutoff = int(np.ceil(len(terrorism_data) * percentage_test))
    terrorism_train, terrorism_test = terrorism_data[terrorism_cutoff:], terrorism_data[:terrorism_cutoff]
    safe_cutoff = int(np.ceil(len(safe_data) * percentage_test))
    safe_train, safe_test = safe_data[safe_cutoff:], safe_data[:safe_cutoff]


    TP, FP, FN, TN = 0, 0, 0, 0
    TP_tweet, FP_tweet, FN_tweet, TN_tweet = [], [], [], []
    print("evaluating terrorism")
    for terrorism_tweet in terrorism_test:
        result = classify(terrorism_tweet,
                          np.random.choice(terrorism_train, size=3, replace=False),
                          np.random.choice(safe_train, size=3, replace=False))
        if result == "terrorism":
            TP += 1
            TP_tweet.append([terrorism_tweet])
        elif result == "safe":
            FN += 1
            FN_tweet.append([terrorism_tweet])
            print(terrorism_tweet)
        else:
            print(result)

    print("evaluating safe tweets")
    print(len(safe_test))
    for safe_tweet in safe_test:
        print(safe_tweet)
        result = classify(safe_tweet,
                          np.random.choice(terrorism_train, size=3, replace=False),
                          np.random.choice(safe_train, size=3, replace=False))
        if result == "terrorism":
            FP += 1
            FP_tweet.append([safe_tweet])
            print(safe_tweet)
        elif result == "safe":
            TN += 1
            TN_tweet.append([safe_tweet])
        else:
            print(result)

    print(TP, FP, FN, TN)

    filename = "tweets_classified.csv"

    with open(filename, 'w') as csvfile: 
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(TP_tweet)
        csvwriter.writerows([[f'TP: {TP}']])
        csvwriter.writerows(FN_tweet)
        csvwriter.writerows([[f'FN: {FN}']])
        csvwriter.writerows(FP_tweet)
        csvwriter.writerows([[f'FP: {FP}']])
        csvwriter.writerows(TN_tweet)
        csvwriter.writerows([[f'TN: {TN}']])

evaluate(terrorism_data, safe_data, percentage_test=0.01)