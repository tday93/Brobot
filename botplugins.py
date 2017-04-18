import subprocess
import os
import random
import requests
import urllib
import datetime
import json
import string
import re
import yaml

with open("SECRETS.yaml", "r") as filein:
    secrets = yaml.load(filein)

tumblr_api_key = secrets['tumblrapi']


class BotPlugins(object):

    def __init__(self):

        self.commands = {
                "!channel":self.whichchannel,
                "!add":self.adddjbrobot,
                "!smut":self.smut,
                "butter me up scotty":self.scotty,
                "sfw sasuke":self.sasuke,
                "!brobot": self.addfactoid,
                "!brobotreact": self.addreaction,
                "!addquote": self.addquote,
                "!getquote": self.getquote,
                "!add": self.adddjbrobot,
                "!memeplease": self.memeplease,
                "!delete":self.deleteself,
                "!addtitle":self.add_job_title,
                "!give": self.fill_pockets,
                "!take":self.empty_pockets,
                "!pockets":self.list_pockets

                }
        self.band_chance = 15

    async def list_pockets(self, message):
        if len(self.miscdata["pockets"]) <1:
            await self.safe_send_message(message.channel, "My pockets are empty")
            return
        msg = "I have a "
        for item in self.miscdata["pockets"]:
            msg = msg + "{} and a ".format(item)
        msg = msg[:-6]
        await self.safe_send_message(message.channel, msg)
    async def fill_pockets(self, message):
        item = message.content.split(' ', 1)[1]
        if len(self.miscdata["pockets"]) >= 5:
            discarded = self.miscdata["pockets"].pop([0])
            self.miscdata["pockets"].append(item)
            msg = "Okay {}, I threw away my {} and took {}".format(message.author.mention, discarded, item)
            await self.safe_send_message(message.channel, msg)
        else:
            self.miscdata["pockets"].append(item)
            msg = "Thanks for the {}, {}".format(item, message.author.mention)
            await self.safe_send_message(message.channel, msg)

    async def empty_pockets(self, message):
        if len(self.miscdata["pockets"]) <1:
            await self.safe_send_message(message.channel, "My pockets seem to be empty")
            return
        item = random.choice(self.miscdata["pockets"])
        self.miscdata["pockets"].remove(item)
        msg = "Here {}, have a {}".format(message.author.mention, item)
        await self.safe_send_message(message.channel, msg)

    async def add_job_title(self, message):

        title =  message.content.split(' ', 1)[1]
        self.miscdata["jobtitles"].append(title)
        msg = 'Added "{}" to my list of job titles'.format(title)
        await self.safe_send_message(message.channel, msg)

    async def get_response(self,message):

        await self.bandnames(message)
        first = message.content.split(' ')[0]
        if message.content in self.commands:
            await self.commands[message.content](message)

        elif first in self.commands:
            await self.commands[first](message)

        await self.getfactoid(message)
        await self.getreaction(message)

    def is_me(self, message):
        return message.author == self.user

    async def deleteself(self, message):
        number = int(message.content.split(' ')[1])
        await self.purge_from(message.channel, limit = number, check=is_me)


    async def bandnames(self, message):
        if message.content.startswith("!") or message.content.startswith("*"):
            return
        t = message.content.casefold()
        q = t.split(' ')
        s = [re.sub(r'\W+', '', item) for item in q]
        print(s)
        print(len(s))
        if len(s) == 3:
            if s in self.bands['band names']:
                print("this already exists, skipping")
                return
            else:
                i = random.randrange(0, self.band_chance)
                print(i)
                self.bands["band names"].append(s)
                if i == 0:
                    msg = "https://{}{}{}.tumblr.com".format(s[0],s[1],s[2])
                    await self.safe_send_message(message.channel, msg)
                    self.bands["good band names"].append(s)
                    self.band_chance = 15
                    return
                self.band_chance = self.band_chance -1
                print(self.band_chance)
                return

    async def whichchannel(self, message):
        await self.safe_send_message(message.channel, message.channel)

    async def adddjbrobot(self, message):
        mods = ["cucksquad", "crunchwrap supreme", "prok"]
        roles = []
        for role in message.author.roles:
            roles.append(role.name)
        print(roles)
        print(message.content)
        if  len(set(roles).intersection(mods)) <1 :
            await self.safe_send_message(message.channel,"I can't let you do that dave")
            return
        link = message.content.split(' ')[1]
        with open("DJBROBOT/MusicBot/config/autoplaylist.txt","a") as f:
            f.write(link +"\n")

    async def smut(self, message):
        if str(message.channel) !="general":
            msg = subprocess.run(['python', '/home/tday/projects/chatbots/markov.py'], stdout=subprocess.PIPE).stdout.decode('utf-8')
            await self.safe_send_message(message.channel, msg)
        else:
            await self.safe_send_message(message.channel, "Not in here buddy")

    async def scotty(self, message):
        r = requests.get('https://api.tumblr.com/v2/tagged?tag=scotty&api_key={0}'.format(tumblr_api_key))
        scottydict = r.json()
        pic_list=[]
        for item in scottydict['response']:
            if item['type'] == 'photo':
                for pic in item['photos']:
                    if 'original_size' in pic:
                        pic_list.append(pic['original_size']['url'])


        scotty = random.choice(pic_list)
        await self.safe_send_message(message.channel ,scotty)


    async def memeplease(self, message):
        tag = message.content.split(' ',1)[1]
        r = requests.get('https://api.tumblr.com/v2/tagged?tag={}&api_key={}'.format(tag, tumblr_api_key))
        memedict = r.json()
        pic_list=[]
        for item in memedict['response']:
            if item['type'] == 'photo':
                for pic in item['photos']:
                    if 'original_size' in pic:
                        pic_list.append(pic['original_size']['url'])

        if len(pic_list) < 1:
            await self.safe_send_message(message.channel, "I'm sorry I couldn't find anything for the tag: {}".format(tag))
            return
        meme = random.choice(pic_list)
        await self.safe_send_message(message.channel ,meme)

    async def butter(self, message):
        await self.safe_send_file(messgae.channel,'butter.jpg')

    async def sasuke(self, message):
        msg = await self.safe_send_file(message.channel,'SFWSASUKE.png')
        await self.safe_add_reaction(msg, "💯")
        await self.safe_add_reaction(msg, "😍")
        await self.safe_add_reaction(msg, "👌")

    async def addquote(self, message):
        if len(message.mentions) != 1:
            await self.safe_send_message(message.channel, 'I can only quote one user at once')
        user = message.mentions[0]
        if user.id not in self.qdb:
            self.qdb[user.id] = {"name":user.name, "discriminator":user.discriminator, "quotes": []}
        query = message.content.split(' ', 2)[2].strip()
        quotes = []
        for message in self.messages:
            if message.author.id == user.id and message.content.startswith(query):
                quotes.append(message)
        if len(quotes) != 1:
            await self.safe_send_message( message.channel, "You'll have to be more specific")
        self.qdb[user.id]["quotes"].append(quotes[0].content)

        await self.safe_send_message(message.channel, 'Quoted {} saying: "{}"'.format(user.mention, quotes[0].content))

    async def getquote(self, message):
        print(self.qdb)
        if len(message.mentions) != 1:
            return BResponse('text', message, "I can only retrieve quotes from one user at a time")
        user = message.mentions[0]
        if user.id not in self.qdb:
            return BResponse('text', message, "I don't have any quotes from that user.")
        quotes = self.qdb[user.id]["quotes"]
        quote = random.choice(quotes)
        msg = '{} said: "{}"'.format(user.mention,quote)
        await self.safe_send_message(message.channel, msg)

    async def addfactoid(self, message):

        t = message.content.split(' ', 1)[1].split("<is>")
        trigger = t[0].strip()
        factoid = t[1].strip()
        if len(trigger) <1 or len(factoid) <1:
            return self.safe_send_message(message.channel, "I dont understand that")

        if trigger in self.fdb:
            existing = self.fdb[trigger]
            if type(existing) is str:
                l = [existing, factoid]
                self.fdb[trigger] = l

            else:
                self.fdb[trigger].append(factoid)
        else:
            self.fdb[trigger] = []
            self.fdb[trigger].append(factoid)
        msg = "Okay {}, {} is {}".format(message.author.mention, trigger, factoid)
        await self.safe_send_message(message.channel, msg)

    async def getfactoid(self, message):
        t = message.content
        if t in self.fdb:
            r = random.choice(self.fdb[t])
            if "$who" in r:
                if message.author.nick != None:
                    name = message.author.nick
                else:
                    name = message.author.name
                r = r.replace("$who", name)
            if "$someone" in r:
                person = random.choice(list(message.server.members))
                r = r.replace("$someone", person.mention)
            if "$digit" in r:
                r = r.replace("$digit", str(random.randrange(0, 9)))
            if "$job" in r:
                r = r.replace("$job", random.choice(self.miscdata["jobtitles"]))
            if "$item" in r:
                r = r.replace("$item", random.choice(self.miscdata["pockets"]))
            await self.safe_send_message(message.channel, r)


    async def addreaction(self, message):
        mods = ["cucksquad", "crunchwrap supreme", "prok"]
        roles = []
        for role in message.author.roles:
            roles.append(role.name)
        if  len(set(roles).intersection(mods)) <1 :
            await self.safe_send_message(message.channel, "I can't let you do that dave")
            return

        t = message.content.split(' ', 1)[1]

        tl = t.split('<is>')
        print(tl)
        if len(tl) != 2:
            await self.safe_send_message(message.channel, "Something went wrong")

        trigger = tl[0].strip()
        factoid = tl[1].strip()

        if trigger in self.rdb:
            existing = self.rdb[trigger]
            if type(existing) is str:
                l = [existing, factoid]
                self.rdb[trigger] = l

            else:
                self.rdb[trigger].append(factoid)
        else:
            self.rdb[trigger] = []
            self.rdb[trigger].append(factoid)

    async def getreaction(self, message):
        t = message.content
        if t in self.rdb:
            await self.safe_add_reaction(message, random.choice(self.rdb[t]))

    def writejson(self,path, jd):
        with open(path, 'w') as outfile:
            json.dump(jd, outfile, indent=2, sort_keys=True, separators=(',',':'))

    def getjson(self, path):
        with open(path) as fn:
            jd = json.load(fn)
        return jd


