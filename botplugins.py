import subprocess
import random
import requests
import re
import yaml
import googleimages

with open("SECRETS.yaml", "r") as filein:
    secrets = yaml.load(filein)

tumblr_api_key = secrets['tumblrapi']

""" 
This is the dark pit i threw all of the chat bots plugins into.

The client object inherits everything from this object, and everything should be
in the same scope.
"""


class BotPlugins(object):

    def __init__(self):

        """
        This is a mapping of commands given in chat to functions in this class.
        Really anything should work but know that each message will check for 
        both == any of the below keys, or startswith() any of the below keys


        Shorter is better than long, anything not matching "!<something>" should
        be there for either a good reason or a good joke
        """

        self.commands = {
                "!channel": self.whichchannel,
                "!add": self.adddjbrobot,
                "!smut": self.smut,
                "butter me up scotty": self.scotty,
                "sfw sasuke": self.sasuke,
                "!brobot": self.addfactoid,
                "!brobotreact": self.addreaction,
                "!addquote": self.addquote,
                "!getquote": self.getquote,
                "!memeplease": self.memeplease,
                "!delete": self.deleteself,
                "!addtitle": self.add_job_title,
                "!give": self.fill_pockets,
                "!take": self.empty_pockets,
                "!pockets": self.list_pockets,
                "!addlib": self.addlib,
                "!addcat": self.addcat,
                "!categories": self.madcats,
                "!swearjar": self.swearjar,
                "!addregex": self.add_regex

                }
        # the starting chance that he will mention something is a good band name
        self.band_chance = 15

    async def madcats(self, message):
        """ Lists current vailable madlib catergories
        """
        cats = []
        for k, v in self.miscdata["madlib"].items():
            cats.append(k)
        s_cats = " ".join(cats)
        msg = "My current madlib categories are: {}".format(s_cats)
        await self.safe_send_message(message.channel, msg)

    async def swearjar(self, message):
        dollas =float(self.miscdata["swearjar"]) / 100
        dollars = "${:,.2f}".format(dollas)
        msg = "There is {} in the swear jar".format(dollars)
        await self.safe_send_message(message.channel, msg)

    async def addlib(self, message):
        """
        Adds a give word to a given madlib category with format
        '!addlib <category> <word>'
        """
        s = message.content.split(' ', 2)
        if s[1] not in self.miscdata["madlib"]:
            await self.safe_send_message(message.channel, "I'm sorry thats not a category.... yet")
            return
        else:
            self.miscdata["madlib"][s[1]].append(s[2])
            msg = "Okay {}, {} added to {}".format(message.author.mention, s[2], s[1])
            await self.safe_send_message(message.channel, msg)

    async def addcat(self, message):
        """
        Adds a category to the madlib categories 
        Currently will only allow me to do this
        """
        if message.author.id != "204378458393018368":
            await self.safe_send_message(message.channel, 
                                         "I'm sorry but I can't do that Dave")
        else:
            cat = message.content.split(' ')[1]
            if cat[0] != "$":
                await self.safe_send_message(message.channel, 
                                             "The category should start with $")
                return
            if cat not in self.miscdata["madlib"]:
                self.miscdata["madlib"][cat] = []
                await self.safe_send_message(message.channel, 
                                             "{} madlib category added".format(cat))
            else:
                await self.safe_send_message(message.channel, 
                                             "That category already exists")

    async def list_pockets(self, message):
        """"
        Lists what are in his poeckts
        """
        if len(self.miscdata["pockets"]) < 1:
            await self.safe_send_message(message.channel, "My pockets are empty")
            return
        msg = "I have "
        for item in self.miscdata["pockets"]:
            msg = msg + "{} and ".format(item)
        msg = msg[:-5]
        await self.safe_send_message(message.channel, msg)

    async def fill_pockets(self, message):
        """
        Takes an item and puts it in his pockets.
        If he has too many items in his pockets he'll throw one away first
        """
        item = message.content.split(' ', 1)[1]
        if len(self.miscdata["pockets"]) >= 5:
            discarded = self.miscdata["pockets"].pop(0)
            self.miscdata["pockets"].append(item)
            msg = "Okay {}, I threw away my {} and took {}".format(
                message.author.mention, discarded, item)
            await self.safe_send_message(message.channel, msg)
        else:
            self.miscdata["pockets"].append(item)
            msg = "Thanks for the {}, {}".format(item, message.author.mention)
            await self.safe_send_message(message.channel, msg)

    async def empty_pockets(self, message):
        """
        Removes an item from his pockets at random and gives it to the person
        who asked
        """
        if len(self.miscdata["pockets"]) < 1:
            await self.safe_send_message(message.channel, "My pockets seem to be empty")
            return
        item = random.choice(self.miscdata["pockets"])
        self.miscdata["pockets"].remove(item)
        msg = "Here {}, have a {}".format(message.author.mention, item)
        await self.safe_send_message(message.channel, msg)

    async def add_job_title(self, message):

        """
        legacy custom function that should be deprecated in favor of madlibs
        """
        title = message.content.split(' ', 1)[1]
        self.miscdata["madlib"]["$job"].append(title)
        msg = 'Added "{}" to my list of job titles'.format(title)
        await self.safe_send_message(message.channel, msg)

    async def add_regex(self, message):
        
        if message.author.id != "204378458393018368":
            msg = "I'm sorry but I can't do that Dave"
            await self.safe_send_message(message.channel, msg)
            return
        split_message = message.content.split(" ", 2)
        if len(split_message) != 3:
            await self.safe_send_message(message.channel, "Something went wrong")
            return
        reg_trigger = split_message[1]
        reg_factoid = split_message[2]
        if reg_trigger not in self.miscdata["regices"]:
            self.miscdata["regices"][reg_trigger] = []
        self.miscdata["regices"][reg_trigger].append(reg_factoid)
        msg = "Okay $who, I'll repond to a message matching {} with {}".format(
                                                                    reg_trigger,
                                                                    reg_factoid
                                                                    )
        await self.safe_send_message(message.channel, msg)

    async def regex_responses(self, message):
        regices = self.miscdata["regices"]
        for k, v in regices.items():
            pattern = re.compile(k)
            if pattern.match(message.content):
                response = random.choice(v)
                
                s = [self.madlibword(message, word) for word in response.split(' ')]
                msg = " ".join(s)
                await self.safe_send_message(message.channel, msg)
    
    async def get_response(self, message):

        """
        Core routing function. 
            1. checks for band name
            2. checks for commands
            3. checks for regex matches
            4. checks for factoids
        """
        await self.bandnames(message)
        first = message.content.split(' ')[0]
        if message.content in self.commands:
            await self.commands[message.content](message)

        elif first in self.commands:
            await self.commands[first](message)
        await self.regex_responses(message)
        await self.getfactoid(message)
        await self.getreaction(message)

    def is_me(self, message):
        return message.author == self.user

    async def deleteself(self, message):
        """
        deletes his own messages, 
        mainly used in case of accidental NSFW content
        """
        number = int(message.content.split(' ')[1])
        await self.purge_from(message.channel, limit=number, check=is_me)

    async def bandnames(self, message):
        """
        looks for odd three-word combinations and occasionally remarks on one
        each combination whether remarked on or not gets stored, and will never
        be mentioned again
        """
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
                    msg = "https://{}{}{}.tumblr.com".format(s[0], s[1], s[2])
                    await self.safe_send_message(message.channel, msg)
                    self.bands["good band names"].append(s)
                    self.band_chance = 15
                    return
                self.band_chance = self.band_chance - 1
                print(self.band_chance)
                return

    async def whichchannel(self, message):
        await self.safe_send_message(message.channel, message.channel)

    async def adddjbrobot(self, message):
        """
        Adds a given youtube link to the autoplaylist of our dj bot,
        only lets mods on the current server do so
        """
        mods = ["cucksquad", "crunchwrap supreme", "prok"]
        roles = []
        for role in message.author.roles:
            roles.append(role.name)
        print(roles)
        print(message.content)
        if len(set(roles).intersection(mods)) < 1:
            await self.safe_send_message(message.channel, "I can't let you do that dave")
            return
        link = message.content.split(' ')[1]
        with open("DJBROBOT/MusicBot/config/autoplaylist.txt", "a") as f:
            f.write(link + "\n")

    async def smut(self, message):
        if str(message.channel) !="general":
            msg = subprocess.run(['python', '/home/tday/projects/chatbots/markov.py'], stdout=subprocess.PIPE).stdout.decode('utf-8')
            await self.safe_send_message(message.channel, msg)
        else:
            await self.safe_send_message(message.channel, "Not in here buddy")

    async def scotty(self, message):
        """
        finds a stupid picture of scotty from star trek and posts it
        mostly a single-case example of the memeplease function
        """
        r = requests.get('https://api.tumblr.com/v2/tagged?tag=scotty&api_key={0}'.format(tumblr_api_key))
        scottydict = r.json()
        pic_list= []
        for item in scottydict['response']:
            if item['type'] == 'photo':
                for pic in item['photos']:
                    if 'original_size' in pic:
                        pic_list.append(pic['original_size']['url'])
        scotty = random.choice(pic_list)
        await self.safe_send_message(message.channel, scotty)

    async def memeplease(self, message):
        """
        searches tumblr and occasionally google images for a picture using
        a provided string, and posts it into chat.
        """
        tag = message.content.split(' ',1)[1]
        r = requests.get('https://api.tumblr.com/v2/tagged?tag={}&api_key={}'.format(tag, tumblr_api_key))
        memedict = r.json()
        pic_list=[]
        for item in memedict['response']:
            if item['type'] == 'photo':
                for pic in item['photos']:
                    if 'original_size' in pic:
                        pic_list.append(pic['original_size']['url'])
        
        if len(pic_list) < 5:
            g_images = googleimages.get_images(tag)
            pic_list = pic_list + g_images
        if len(pic_list) < 1:
            await self.safe_send_message(message.channel, "I'm sorry I couldn't find anything for the tag: {}".format(tag))
            return
        meme = random.choice(pic_list)
        await self.safe_send_message(message.channel, meme)

    async def butter(self, message):
        await self.safe_send_file(message.channel, 'butter.jpg')

    async def sasuke(self, message):
        msg = await self.safe_send_file(message.channel, 'SFWSASUKE.png')
        await self.safe_add_reaction(msg, "💯")
        await self.safe_add_reaction(msg, "😍")
        await self.safe_add_reaction(msg, "👌")

    async def addquote(self, message):
        """
        searches for a given quote by a given user and saves it.
        format is "!addquote @user <exact start of message>"
        """
        if len(message.mentions) != 1:
            await self.safe_send_message(message.channel, 'I can only quote one user at once')
        user = message.mentions[0]
        if user.id not in self.qdb:
            self.qdb[user.id] = {"name": user.name, "discriminator": user.discriminator, "quotes": []}
        query = message.content.split(' ', 2)[2].strip()
        quotes = []
        for message in self.messages:
            if message.author.id == user.id and message.content.startswith(query):
                quotes.append(message)
        if len(quotes) != 1:
            await self.safe_send_message(message.channel, "You'll have to be more specific")
        self.qdb[user.id]["quotes"].append(quotes[0].content)

        await self.safe_send_message(message.channel, 'Quoted {} saying: "{}"'.format(user.mention, quotes[0].content))

    async def getquote(self, message):
        """
        returns a random quote from a given user
        """
        print(self.qdb)
        if len(message.mentions) != 1:
            await self.safe_send_message(message.channel,
                                "I can only retrieve quotes from one user at a time")
        user = message.mentions[0]
        if user.id not in self.qdb:
            await self.safe_send_message(message.channel,
                                "I don't have any quotes from that user.")
        quotes = self.qdb[user.id]["quotes"]
        quote = random.choice(quotes)
        msg = '{} said: "{}"'.format(user.mention, quote)
        await self.safe_send_message(message.channel, msg)

    async def addfactoid(self, message):
        """
        Adds a given factoid to his database. format is:
            !brobot [trigger] <is> [factoid]
        """

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
        """"
        searches the factoid database for a given trigger and responds
        with a random factoid associated with that trigger
        """
        t = message.content
        pattern = re.compile("\$\w*")
        if t in self.fdb:
            r = random.choice(self.fdb[t])

            s = [self.madlibword(message, word) for word in r.split(' ')]
            msg = " ".join(s)

            await self.safe_send_message(message.channel, msg)

        elif pattern.search(t) is not None and not t.startswith("!"):
            s = [self.madlibword(message, word) for word in t.split(' ')]
            if s != t.split(' '):
                msg = " ".join(s)
                await self.safe_send_message(message.channel, msg)

    def madlibword(self, message, stringIn):
        """
        looks for madlib categories associated with the supplied word and swaps 
        them out as necessary
        """
        self.madlib = self.miscdata["madlib"]
        if stringIn.startswith("$swearjar"):
            self.miscdata["swearjar"] = self.miscdata["swearjar"] + 25
            return ""
        if stringIn.startswith("$who"):
            if message.author.nick != None:
                name = message.author.nick
            else:
                name = message.author.name
            return name
        if stringIn.startswith("$someone"):
            person = random.choice(list(message.server.members))
            return person.mention
        if stringIn.startswith("$digit"):
            return str(random.randrange(0, 9))
        if stringIn.startswith("$item"):
                return random.choice(self.miscdata["pockets"])
        for k,v in self.madlib.items():
            if stringIn.startswith(k):
                return random.choice(v)
        else:
            return stringIn

    async def addreaction(self, message):
        """
        similar to add factoide but responds with a discord reaction rather than
        a message
        """
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
        """
        similar to getfactoid but for reactions
        """
        t = message.content
        if t in self.rdb:
            await self.safe_add_reaction(message, random.choice(self.rdb[t]))
