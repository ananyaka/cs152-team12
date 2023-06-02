# This is example code using GPT-4 to do a basic classification of a text string
# It is super basic, your milestone 3 should do better than this
# This is a live API key that should be used only for the CS 152 project
# Please do not check the API key into a public GitHub repo or share it with anybody outside of your group


import os
import openai
import json
# print(openai.Model.list()) # Can used to verify GPT-4 access


class Detector():

    def __init__(self):
        # There should be a file called 'tokens.json' inside the same folder as this file
        token_path = 'tokens.json'
        if not os.path.isfile(token_path):
            raise Exception(f"{token_path} not found!")
        with open(token_path) as f:
            # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
            tokens = json.load(f)
            openai.organization = tokens['openai_organization']
            openai.api_key = tokens['openai_api_key']

    def classify(self, message):

        response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
        {"role": "system", "content": "You are a content moderation system. Classify each input as either terrorism or safe."},
        {"role": "user", "content": "AQAP: 'RESPONSE TO SHEIKH BAGHDADIS STATEMENT 'ALTHOUGH THE DISBELIEVERS DISLIKE IT.'"},
        {"role": "assistant", "content": "terrorism"},
        {"role": "user", "content": "Matty Jordan lives at the Scott research station in Antarctica and tried to pour a can of Coke when it was -57°C"},
        {"role": "assistant", "content": "safe"},
        {"role": "user", "content": "Aslm, anybody translating the new JN video? Will translate it if  nobody else is @IbnNabih1 @KhalidMaghrebi_ @MuwMedia @Polder_Mujahid"},
        {"role": "assistant", "content": "terrorism"},
        {"role": "user", "content": "Quantum levitation and quantum locking are a consequence of the Meissner effect and allow superconductor to glide freely over a track of magnets"},
        {"role": "assistant", "content": "safe"},
        {"role": "user", "content": "@Skxx51 he can't accept the mubahala between Sh Adnani &amp; Abu Abdullah Shami where the truth is on IS @striv3ric @War_Reports (2)"},
        {"role": "assistant", "content": "terrorism"},
        {"role": "user", "content": "Everyone should learn to fine-tune LLMs.\n You can try (and fail) to force GPT-4 on to every solution, or you can reduce your costs and improve your accuracy by fine-tuning a task-specific LLM.\n Here's why, and some tips for getting started:"},
        {"role": "assistant", "content": "safe"},
        {"role": "user", "content": message}
        ]
        )

        output = response['choices'][0]['message']['content']
        return output