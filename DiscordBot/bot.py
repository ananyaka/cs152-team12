# bot.py
import discord
from discord.ext import commands
from enum import Enum, auto
import os
import json
import logging
import re
import requests
from report import Report
import pdb
from chatgpt import Detector 

from uni2ascii import uni2ascii
# setting up reactions
intents = discord.Intents.default()
intents.reactions = True

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']

#variables
sensitive_keywords = ["terrorism", "isis", "911"]
userList = {} #leave empty
urgent_rules = ["detonate the bomb","attack tomorrow", "kill everyone", "everyone will die"]
suspicous_rules = ["isis","terrorism is not bad"]
mid_rules = ["bomb", "bombs","i love isis", "come join isis", "join isis"]

class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.detector = Detector()

        self.currentMessage = None
        self.currentAbuser = None
    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return
        #create user profile if user does not exist
        await self.create_userSpecs(message)
        
        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
            await self.platform_rules(message)
        else:
            await self.handle_dm(message)

            
    async def create_userSpecs(self, message):
        user_id = message.author.id
        user_name = message.author.name
        
        #if user already exists, do nothing
        if user_id in userList:
            return
            #if a new user, create user
        else:
            userList[user_id] = {
            "name": user_name,
            "red_flags": 0,
            "yellow_flags": 0,
            "green_flags": 0
            }
            
        #checking all users created - allow moderator to view users (uncomment)
        mod_channel = self.mod_channels[message.guild.id]
        await mod_channel.send(f'users created:')
        count = 1
        for key in userList:
            await mod_channel.send(f'user {count}:\n{userList[key]}')
            count+=1



    async def platform_rules(self, message):
        text = message.content 
        text = text.lower()  
        user_id = message.author.id
        mod_channel = self.mod_channels[message.guild.id]

        urgent = 0
        mid = 0
        sus = 0

        #urgent rules
        for x in urgent_rules:
            testRule = re.search(x, text)

            if testRule:
                urgent += 1
            else:
                continue

        #mid rules       
        for x in mid_rules:
            testRule = re.search(x, text)

            if testRule:
                mid +=1
                
            else:
                continue

        #suspicous  rules       
        for x in suspicous_rules:
            testRule = re.search(x, text)

            if testRule:
                sus +=1  
            else:
                continue
        
        #calculate total score & flag
        total = (urgent*5) + (mid*3) + (sus*0.5)
        await mod_channel.send(f'testing rules...')
        await mod_channel.send(f'comment: {text}')
        await mod_channel.send(f'total score: {total}')

        if total < 10:
            if total>=5:
                userList[user_id]["red_flags"] += 1
            elif total <5 and total >=3:
                userList[user_id]["yellow_flags"] += 1
            elif total < 3:
                userList[user_id]["green_flags"] += 1
    
        elif total >= 10 and total < 20:
            if total>=15:
                userList[user_id]["red_flags"] += 1
            elif total <15 and total >=13:
                userList[user_id]["yellow_flags"] += 1
            elif total < 13 and total >= 10:
                userList[user_id]["green_flags"] += 1

        elif total >= 20:
            if total>=25:
                userList[user_id]["red_flags"] += 1
            elif total <25 and total >=23:
                userList[user_id]["yellow_flags"] += 1
            elif total < 23 and total >= 20:
                userList[user_id]["green_flags"] += 1


        #checking all users created - allow moderator to view users and their flags (uncomment)
        count = 1
        for key in userList:
            await mod_channel.send(f'user {count}:\n{userList[key]}')
            count+=1  

        
        
    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # Only respond to messages if they're part of a reporting flow
        print(message.content)
        if author_id not in self.reports and not message.content.startswith(Report.START_KEYWORD):
            return

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Let the report class handle this message; forward all the messages it returns to us
        responses = await self.reports[author_id].handle_message(message)
        for r in responses:
            await message.channel.send(r)

        # If the report is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete():
            for guild_id, mod_channel in self.mod_channels.items():
                await mod_channel.send(f'User reported the following message:\n{self.reports[author_id].abuse_message_link}')
                await mod_channel.send(f'The message was: {self.reports[author_id].abuse_message.content}')
                await mod_channel.send(f'The message was reported for: {self.reports[author_id].abuse_type}')
                if self.reports[author_id].additional_context_message is not None:
                    await mod_channel.send(f'There\'s additional context with this report: {self.reports[author_id].additional_context_message.content}')
                print(self.reports[author_id].abuse_message)
                self.currentAbuser = self.reports[author_id].abuse_message.author
                self.currentMessage = self.reports[author_id].abuse_message
                await mod_channel.send(f'React 😞 for permanently banning the user, or 😤 for temporarily banning the user for 72 hours, or 😀 to end the review and issue a warning. These reactions will also delete the user\'s message')


            self.reports.pop(author_id)

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" channel
        if not message.channel.name == f'group-{self.group_num}':
            return

        ascii_string = uni2ascii(message.content)
        if any(word in sensitive_keywords for word in ascii_string.split()):

            # Forward the message to the mod channel
            mod_channel = self.mod_channels[message.guild.id]
            await mod_channel.send(f'Detected message potentially related to terrorism:\n{message.author.name}: "{message.content}"')
            scores = self.eval_text(message.content)
            await mod_channel.send(self.code_format(scores))
            print(self.detector.classify(scores))

    async def on_raw_reaction_add(self, payload):
        channel = await self.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if (str(channel) != f'group-{self.group_num}-mod') and (message != 'React 😞 for permanently banning the user, or 😤 for temporarily banning the user for 72 hours, or 😀 to end the review and issue a warning.'):
            return
        
        # delete the message if we react to the previous message.
        if (payload.emoji.name == '😞' or payload.emoji.name == '😤' or payload.emoji.name == '😀'):
            if (self.currentMessage != None):
                await self.currentMessage.delete()
        channel_dm = ''
        abuser_dm = ''
        if (payload.emoji.name == '😞') :
            channel_dm += "This user is permanently banned."
            abuser_dm += 'Your following post violates our content policies:\n' + self.currentMessage.content + '\nYou have been permanently banned because you have violated our content policies three separate times.'
        elif (payload.emoji.name == '😤') :
            channel_dm += "This user is temporarily banned. They can return to the app in 72 hours."
            abuser_dm += 'Your following post violates our content policies:\n' + self.currentMessage.content + "\nYou are now temporarily banned for violating our content policy for the second time. You may log back in after 72 hours. If you violate our policy again, you will be permanently banned."
        elif (payload.emoji.name == '😀') :
            channel_dm += "This user will be issued a warning. "
            abuser_dm += 'Your following post violates our content policies: \n' + self.currentMessage.content + "\nOur team has detected a violation of our content policy in the last message you sent. If you continue to violate our policies, we will issue a temporary ban followed by a permanent ban. "
        if (channel_dm != ""): await channel.send(channel_dm + "The message they sent has been removed.")
        if (self.currentAbuser != None) and abuser_dm != "": await self.currentAbuser.send(abuser_dm)

    async def on_raw_message_edit(self, payload):
        # Only handle messages sent in the "group-#" channel that are edited
        channel = await self.fetch_channel(payload.channel_id)
        channel_name = channel.name
        if not channel_name == f'group-{self.group_num}':
            return

        message = await channel.fetch_message(payload.message_id)
        ascii_string = uni2ascii(message.content)

        # Perform desired actions
        if any(word in sensitive_keywords for word in ascii_string.split()):
            # Forward the message to the mod channel
            mod_channel = self.mod_channels[payload.guild_id]
            await mod_channel.send(f'Detected edited message potentially related to terrorism:\n{message.author.name}: "{message.content}"')
            scores = self.eval_text(message.content)
            await mod_channel.send(self.code_format(scores))
    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return uni2ascii(message)

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text + "'"


client = ModBot()
client.run(discord_token)
