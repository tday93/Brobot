import discord
import argparse
import logging
import random
import yaml
import atexit
import time
import json
import sys
import zalgo
import requests
from bs4 import BeautifulSoup
import re
import googleimages

with open("SECRETS.yaml", "r") as filein:
    secrets = yaml.load(filein)

tumblr_api_key = secrets['tumblrapi']

# argparse setup for commandline args
parser = argparse.ArgumentParser()
parser.add_argument(
    "-l", "--loglevel",
    help="Choose logging level: DEBUG INFO WARNING ERROR CRITICAL",
    default="DEBUG",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
parser.add_argument("-f", "--filename",
                    help="file to log to, defualt is 'brobot.log'",
                    default="brobot.log")
args = parser.parse_args()


# setup logging
logger = logging.getLogger("brobotlog")
formatter = logging.Formatter(fmt='%(asctime)s %(message)s',
                              datefmt='%m/%d/%Y %I:%M:%S %p')
logger.setLevel(logging.DEBUG)
# file handler for logging
fh = logging.FileHandler(args.filename)
fh.setLevel("DEBUG")
# console handler for logging
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(args.loglevel)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class BroBot(discord.Client):

    def __init__(self):
        self.logger = logging.getLogger("brobotlog")
        self.fdb = self.getjson("factoids.json")
        self.qdb = self.getjson("quotes.json")
        self.rdb = self.getjson("reactions.json")
        self.bands = self.getjson("bands.json")
        self.miscdata = self.getjson("miscdata.json")
        self.commands = {
                "!channel": self.whichchannel,
                "sfw sasuke": self.sasuke,
                "!brobot": self.addfactoid,
                "!brobotreact": self.addreaction,
                "!addquote": self.addquote,
                "!getquote": self.getquote,
                "!memeplease": self.memeplease,
                "!delete": self.deleteself,
                "!give": self.fill_pockets,
                "!take": self.empty_pockets,
                "!pockets": self.list_pockets,
                "!addlib": self.addlib,
                "!addcat": self.addcat,
                "!categories": self.madcats,
                "!swearjar": self.swearjar,
                "!addregex": self.add_regex,
                "!addwordsearch": self.add_wordsearch,
                "!zalgo": self.zalgo_text,
                "!retro": self.retro_text
                }
        # the starting chance that he
        # will mention something is a good band name
        self.band_chance = 30
        super().__init__()

    def cleanup(self):
        self.logger.info("cleaning up")
        self.writejson("factoids.json", self.fdb)
        self.writejson("reactions.json", self.rdb)
        self.writejson("quotes.json", self.qdb)
        self.writejson("bands.json", self.bands)
        self.writejson("miscdata.json", self.miscdata)

    async def on_ready(self):
        self.logger.info("logged in as")
        self.logger.info(self.user.name)
        self.logger.info(self.user.id)
        self.logger.info('-------')

    async def on_message(self, message, num=10):

        if message.author == self.user:
            return
        self.logger.info("Received message: '{}'".format(message.content))
        await self.get_response(message)

    async def safe_send_message(self, dest, content):
        msg = None
        try:
            await self.send_typing(dest)
            time.sleep(1)
            if random.randint(0, 200) == 69:
                content = zalgo.main(content, "NEAR")
            if random.randint(0, 200) == 66:
                content = self.fork_it_up(content)
            self.logger.info("Sending '{}' to {}".format(content, str(dest)))
            msg = await self.send_message(dest, content)
            return msg
        except:
            self.logger.info("nope")

    async def safe_send_file(self, dest, content):
        msg = None
        try:
            msg = await self.send_file(dest, content)
            return msg
        except:
            self.logger.info("Nada")

    async def safe_add_reaction(self, message, content):
        try:
            msg = await self.add_reaction(message, content)
            return msg
        except:
            self.logger.info("no way")

    def writejson(self, path, jd):
        with open(path, 'w') as outfile:
            json.dump(jd, outfile, indent=2,
                      sort_keys=True, separators=(',', ':'))

    def getjson(self, path):
        with open(path) as fn:
            jd = json.load(fn)
        return jd

    """ Utility functions """
    def is_me(self, message):
        return message.author == self.user

    async def guru_meditation(self, message, error):
        await self.safe_send_file(message.channel, "Guru_meditation.gif")
        await self.safe_send_message(message.channel, error)

    def fork_it_up(self, message):
        swaps = [("fuck", "fork"), ("shit", "shirt"), ("ass", "ash")]
        for item in swaps:
            if item[0] in message:
                message.replace(item[0], item[1])
        return message

    async def whichchannel(self, message):
        await self.safe_send_message(message.channel, message.channel)

    def strip_command(self, msg_txt, command):
        stripped_text = msg_txt.split(command + " ", 1)[1]
        return stripped_text

    async def deleteself(self, message):
        """
        deletes his own messages,
        mainly used in case of accidental NSFW content
        """
        number = int(message.content.split(' ')[1])
        await self.purge_from(message.channel, limit=number, check=self.is_me)

    """ Here is where the garbage starts. This is everything to do
        with parsing messages and responding to them appropriately """

    async def get_response(self, message):

        """
        Core routing function.
            1. checks for band name
            2. checks for commands
                a. if command is present, strips invocation and sends to
                    appropriate function
            3. checks for regex matches
            4. checks for factoids
        """
        try:
            # await self.bandnames(message)
            first = message.content.split(' ')[0]

            if message.content in self.commands:
                await self.commands[message.content](message)

            elif first in self.commands:
                await self.commands[first](message)

            await self.regex_responses(message)
            await self.getfactoid(message)
            await self.getreaction(message)
            await self.wordsearch(message)
            await self.goddamnit_eric(message)

        except Exception as inst:
            self.logger.error((type(inst)))
            self.logger.error(inst.args)
            self.logger.error(inst)
            await self.guru_meditation(message, inst.args)

    """ Active commands """

    async def addfactoid(self, message):
        """
        Adds a given factoid to his database. format is:
            !brobot [trigger] <is> [factoid]
        """
        if "sandwich" in message.content.casefold():
            sand_msg = "I am strictly sandwich neutral."
            await self.safe_send_message(message.channel, sand_msg)
            return
        s = self.strip_command(message.content, "!brobot")
        t = s.split("<is>")
        if len(t) <= 1:
            await self.safe_send_message(
                message.channel, "Syntax Error: No <is>")
            return
        trigger = t[0].strip()
        factoid = t[1].strip()
        if len(trigger) < 1 or len(factoid) < 1:
            return self.safe_send_message(
                message.channel, "I dont understand that")

        if trigger in self.fdb:
            self.fdb[trigger].append(factoid)
        else:
            self.fdb[trigger] = [factoid]

        msg = "Okay {}, {} is {}".format(
            message.author.mention, trigger, factoid)
        await self.safe_send_message(message.channel, msg)

    async def addreaction(self, message):
        """
        similar to add factoid but responds
        with a discord reaction rather than
        a message
        """
        mods = ["cucksquad", "crunchwrap supreme", "prok"]
        roles = [role.name for role in message.author.roles]
        if len(set(roles).intersection(mods)) < 1:
            await self.safe_send_message(
                message.channel, "I can't let you do that dave")
            return

        t = self.strip_command(message.content, "!addreaction")
        tl = t.split('<is>')
        if len(tl) != 2:
            await self.safe_send_message(
                message.channel, "Too many is.")

        trigger = tl[0].strip()
        factoid = tl[1].strip()

        if trigger in self.rdb:
            self.rdb[trigger].append(factoid)
        else:
            self.rdb[trigger] = [factoid]

    async def addquote(self, message):
        """
        searches for a given quote by a given user and saves it.
        format is "!addquote @user <part of message>"
        """
        s = self.strip_command(message.content, "!addquote")
        for user in message.mentions:
            if user.id not in self.qdb:
                self.qdb[user.id] = {"name": user.name,
                                     "discriminator": user.discriminator,
                                     "quotes": []}
            query = s.split(" ", 1)[1].strip()
            quotes = [msg for msg in self.messages
                      if msg.author.id == user.id
                      and query in msg.content]

            if len(quotes) == 1:
                self.qdb[user.id]["quotes"].append(quotes[0].content)
                await self.safe_send_message(
                    message.channel,
                    'Quoted {} saying: "{}"'.format(user.mention,
                                                    quotes[0].content))
            else:
                await self.safe_send_message(message.channel,
                                             "You'll have to be more specific")
                return

    async def getquote(self, message):
        """
        returns a random quote from a given user
        """
        for user in message.mentions:
            if user.id not in self.qdb:
                await self.safe_send_message(
                    message.channel, "I don't have any quotes from that user.")
            quotes = self.qdb[user.id]["quotes"]
            if len(quotes) <= 0:
                await self.safe_send_message(
                    message.channel, "I don't have any quotes from that user.")
                return
            quote = random.choice(quotes)
            msg = '{} said: "{}"'.format(user.mention, quote)
            await self.safe_send_message(message.channel, msg)

    async def retro_text(self, message):
        sp_text = message.content.split(" ", 1)[1]
        s_text = sp_text.split("/")
        payload = {"bcg": 5, "txt": 4, "text1": s_text[0],
                   "text2": s_text[1], "text3": s_text[2]}
        r = requests.post(
            "https://m.photofunia.com/categories/all_effects/retro-wave",
            data=payload)
        c = r.content
        soup = BeautifulSoup(c)
        div = soup.find_all("div", {"class": "image full-height-container"})[0]
        img_url = div.find_all("img")[0].get('src')
        await self.safe_send_message(message.channel, img_url)

    async def zalgo_text(self, message):
        text = message.content.split(" ", 1)[1]
        zalgo_text = zalgo.main(text, "NEAR")
        await self.safe_send_message(message.channel, zalgo_text)

    async def madcats(self, message):
        """
        Lists current available madlib catergories
        """
        cats = [k for k, v in self.miscdata["madlib"].items()]
        s_cats = " ".join(cats)
        msg = "My current madlib categories are: {}".format(s_cats)
        await self.safe_send_message(message.channel, msg)

    async def swearjar(self, message):
        dollas = float(self.miscdata["swearjar"]) / 100
        dollars = "${:,.2f}".format(dollas)
        msg = "There is {} in the swear jar".format(dollars)
        await self.safe_send_message(message.channel, msg)

    async def add_wordsearch(self, message):
        s = self.strip_command(message.content, "!addwordsearch")
        t = s.split("<is>")

        if len(t) != 2:
            msg = "Syntax Error: No <is>"
            await self.safe_send_message(message.channel, msg)
            return

        trigger = t[0].strip()
        factoid = t[1].strip()

        if trigger in self.miscdata['wordsearch']:
            self.miscdata['wordsearch'][trigger].append(factoid)
        else:
            self.miscdata['wordsearch'][trigger] = [factoid]
        msg = "Okay {}, I'll repond with {} when I see \"{}\"".format(
            message.author.mention, factoid, trigger)
        await self.safe_send_message(message.channel, msg)

    async def addlib(self, message):
        """
        Adds a give word to a given madlib category with format
        '!addlib <category> <word>'
        """
        s = self.strip_command(message.content, "!addlib")
        s = s.split(" ", 1)
        if s[1] not in self.miscdata["madlib"]:
            await self.safe_send_message(
                message.channel, "I'm sorry thats not a category.... yet")
            return
        else:
            self.miscdata["madlib"][s[1]].append(s[2])
            msg = "Okay {}, {} added to {}".format(
                message.author.mention, s[2], s[1])
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
                await self.safe_send_message(
                    message.channel,
                    "The category should start with $")
                return
            if cat not in self.miscdata["madlib"]:
                self.miscdata["madlib"][cat] = []
                await self.safe_send_message(
                    message.channel,
                    "{} madlib category added".format(cat))
            else:
                await self.safe_send_message(message.channel,
                                             "That category already exists")

    async def list_pockets(self, message):
        """"
        Lists what are in his poeckts
        """
        if len(self.miscdata["pockets"]) < 1:
            await self.safe_send_message(message.channel,
                                         "My pockets are empty")
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
            await self.safe_send_message(message.channel,
                                         "My pockets seem to be empty")
            return
        item = random.choice(self.miscdata["pockets"])
        self.miscdata["pockets"].remove(item)
        msg = "Here {}, have a {}".format(message.author.mention, item)
        await self.safe_send_message(message.channel, msg)

    async def add_regex(self, message):
        """
        lets me and only me add regex responses
        had to restrict this to just myself because otherwise this is
        DANGEROUS
        """
        # check to see if the user adding a regex is tday
        if message.author.id != "204378458393018368":
            msg = "I'm sorry but I can't do that Dave"
            await self.safe_send_message(message.channel, msg)
            return

        # get message minus !addregex command
        base_message = message.content[9:]
        # split message on "~~~" everything before is regex, everything after
        # is response
        split_message = base_message.split("~~~", 1)
        if len(split_message) != 2:
            await self.safe_send_message(
                 message.channel, "Something went wrong")
            return

        reg_trigger = split_message[0]
        reg_factoid = split_message[1]
        if reg_trigger not in self.miscdata["regices"]:
            self.miscdata["regices"][reg_trigger] = []
        self.miscdata["regices"][reg_trigger].append(reg_factoid)

        msg = "Okay $who, I'll repond to a message matching {} with {}".format(
            reg_trigger, reg_factoid)
        await self.safe_send_message(message.channel, msg)

    async def sasuke(self, message):
        msg = await self.safe_send_file(message.channel, 'SFWSASUKE.png')
        await self.safe_add_reaction(msg, "💯")
        await self.safe_add_reaction(msg, "😍")
        await self.safe_add_reaction(msg, "👌")

    async def memeplease(self, message):
        """
        searches tumblr and occasionally google images for a picture using
        a provided string, and posts it into chat.
        """
        tag = message.content.split(' ', 1)[1]
        r = requests.get(
            'https://api.tumblr.com/v2/tagged?tag={}&api_key={}'.format(
                tag, tumblr_api_key))
        memedict = r.json()
        pic_list = []
        for item in memedict['response']:
            if item['type'] == 'photo':
                for pic in item['photos']:
                    if 'original_size' in pic:
                        pic_list.append(pic['original_size']['url'])

        if len(pic_list) < 5:
            g_images = googleimages.get_images(tag)
            pic_list = pic_list + g_images
        if len(pic_list) < 1:

            msg = ("I'm sorry I couldn't "
                   "find anything for the tag: {}").format(tag)
            await self.safe_send_message(message.channel, msg)
            return
        meme = random.choice(pic_list)
        await self.safe_send_message(message.channel, meme)

    """ Passive functions. Each message is passed to these to look for various
        conditions. Brobot may then respond. """

    async def regex_responses(self, message):
        regices = self.miscdata["regices"]
        for k, v in regices.items():
            pattern = re.compile(k)
            if pattern.search(message.content) is not None:
                response = random.choice(v)

                s = [self.madlibword(message, word)
                     for word in response.split(' ')]
                msg = " ".join(s)
                await self.safe_send_message(message.channel, msg)

    async def goddamnit_eric(self, message):
        if message.author.id == "299208991765037066":
            chance = random.randint(1, 100)
            if chance == 1:
                await self.safe_send_message(message.channel, "goddamnit eric")

    async def wordsearch(self, message):
        search_text = message.content.casefold()
        for k, v in self.miscdata['wordsearch'].items():
            if k in search_text:
                response = random.choice(v)
                msg_list = response.split(" ")
                madlib_list = [self.madlibword(message, item)
                               for item in msg_list]
                msg = " ".join(madlib_list)
                await self.safe_send_message(message.channel, msg)

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
        if len(s) == 3:
            if s in self.bands['band names']:
                self.logger.info("this already exists, skipping")
                return
            else:
                i = random.randrange(0, self.band_chance)
                self.bands["band names"].append(s)
                if i == 0:
                    msg = "https://{}{}{}.tumblr.com".format(s[0], s[1], s[2])
                    await self.safe_send_message(message.channel, msg)
                    self.bands["good band names"].append(s)
                    self.band_chance = 30
                    return
                self.band_chance = self.band_chance - 1
                return

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
            if message.author.nick is not None:
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
        for k, v in self.madlib.items():
            if stringIn.startswith(k):
                return random.choice(v)
        else:
            return stringIn

    async def getreaction(self, message):
        """
        similar to getfactoid but for reactions
        """
        t = message.content
        if t in self.rdb:
            await self.safe_add_reaction(message, random.choice(self.rdb[t]))


# open secrets file for API token and start the bot
with open("SECRETS.yaml", 'r') as filein:
    secrets = yaml.load(filein)
bot = BroBot()
bot.run(secrets["token"])


# make sure things get saved to file
@atexit.register
def save_stuff():
    bot.cleanup()
