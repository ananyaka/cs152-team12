from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE1 = auto()
    AWAITING_MESSAGE2 = auto()
    AWAITING_MESSAGE3 = auto()
    MESSAGE_IDENTIFIED1 = auto()
    MESSAGE_IDENTIFIED2 = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE1
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE1:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED1
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "Why are you reporting this content?", \
                      "Use `terrorism` for terrorism " ]
        
        if self.state == State.MESSAGE_IDENTIFIED1:
            self.state = State.AWAITING_MESSAGE2
            return ["What does this post specifically do?", \
                "Use `g&v` Graphic & Violent Content", \
                   "Use `acts` Promotes/Supports Terrorist Acts", \
                    "Use `recruitment` Terrorist Recruitment Content" ]
        
        if self.state == State.AWAITING_MESSAGE2:
            print(message.content)
            if not (message.content == 'acts' or message.content == 'g&v' or message.content == 'recruitment'):
                return ["I'm sorry, I couldn't understand that. Please try again from the options or say `cancel` to cancel."]
            else:
                print("The content is being reported for " + message.content)
                self.state = State.MESSAGE_IDENTIFIED2
                return ["Can you provide additional information?", \
                "Use `yes` for yes ", \
                   "Use `no` for no ", ] 
        
        if self.state == State.MESSAGE_IDENTIFIED2:
            if not (message.content == 'yes' or message.content == 'no'):
                 return ["I'm sorry, I couldn't understand that. Please try again from the options or say `cancel` to cancel."]
            else:
                if message.content == 'yes':
                    self.state = State.AWAITING_MESSAGE3
                    return ["Please tell us the additional information"]
                else:
                    return ["Thank you for reporting. Someone from our team will review this and get back to you shortly"]
        
        if self.state == State.AWAITING_MESSAGE3:
            print("the additional content is " + message.content)
            return ["Thank you for reporting. Someone from our team will review this and get back to you shortly"]

            




        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

