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
        self.fdb = self.getjson("factoid_db.json")
        self.qdb = self.getjson("quotes.json")
        self.bands = self.getjson("bands.json")
        self.miscdata = self.getjson("miscdata.json")
        self.commands = {
                "!channel": self.whichchannel,
                "sfw sasuke": self.sasuke,
                "!brobot": self.add_factoid,
                "!brobotreact": self.add_factoid,
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
                "!addregex": self.add_factoid,
                "!addwordsearch": self.add_factoid,
                "!zalgo": self.zalgo_text,
                "!retro": self.retro_text
                }

        self.matching_functions = {
            "fullstring": self.fullstring_match,
            "substring": self.substring_match,
            "regex": self.regex_match
        }
        # the starting chance that he
        # will mention something is a good band name
        self.band_chance = 80
        super().__init__()

    def cleanup(self):
        self.logger.info("cleaning up")
        self.writejson("factoid_db.json", self.fdb)
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

    # NEW SHIT IS GOING RIGHT HERE

    async def add_factoid(self, message):
        """
            1. determine factoid type
            2. prepare factoid data
            3. add factoid to database
            4. acknowledge addition
        """
        msg_txt = message.content.casefold()

        # determine factoid type
        if msg_txt.startswith("!wordsearch"):
            # substring
            # prepare factoid data
            trigger, response = self.split_factoid(message.content,
                                                   "!wordsearch")
            await self.add_to_fdb(message, trigger, response,
                                  "substring", "text")

        elif msg_txt.startswith("!addreaction"):
            # reactions
            trigger, response = self.split_factoid(message.content,
                                                   "!addreaction")
            await self.add_to_fdb(message, trigger, response,
                                  "substring", "reaction")

        elif msg_txt.startswith("!addregex"):
            # user_regex
            trigger, response = self.split_factoid(message.content,
                                                   "!addregex")
            await self.add_to_fdb(message, trigger, response,
                                  "regex", "text")
        elif msg_txt.startswith("!brobot"):
            # either fullstring or regex
            if "$***" in msg_txt:
                # regex
                trigger, response = self.split_factoid(message.content,
                                                       "!brobot")
                trigger = self.prep_regex(trigger)
                await self.add_to_fdb(message, trigger, response,
                                      "regex", "text")
            else:
                # fulltext
                trigger, response = self.split_factoid(message.content,
                                                       "!brobot")
                await self.add_to_fdb(message, trigger, response,
                                      "fullstring", "text")

    async def add_to_fdb(self, message, trigger, response,
                         trigger_type, response_type):

        factoid = {"trigger_type": trigger_type,
                   "response_type": response_type,
                   "trigger": trigger, "response": response,
                   "user": message.author.id}

        self.fdb.append(factoid)

        msg = "Okay {}, \"{}\" is \"{}\"".format(
            message.author.mention, trigger, response)
        await self.safe_send_message(message.channel, msg)

    def split_factoid(self, msg_txt, command_name, sep="<is>"):
        s = msg_txt.split(command_name, 1)[1]
        t = s.split(sep, 1)
        if len(t) != 2:
            print("ERROR, ERROR")
        else:
            trigger = t[0].strip().casefold()
            response = t[1].strip()
            return trigger, response

    def prep_regex(self, trigger):
        escaped_trigger = re.escape(trigger)
        prepped_trigger = escaped_trigger.replace("\\$\\*\\*\\*", "(\\S+)")
        return prepped_trigger

    async def check_factoid(self, message):
        """
        1. fullstring
        2. substring
        3. regex
        """
        possible_responses = []
        for factoid in self.fdb:
            if self.matching_functions[factoid["trigger_type"]](factoid,
                                                                message):
                possible_responses.append(factoid)
        if len(possible_responses) >= 1:
            chosen_factoid = random.choice(possible_responses)
            # also different response types!
            # madlib stuff still!
            # send messages here
            await self.safe_send_message(message.channel,
                                         chosen_factoid["response"])

    def fullstring_match(self, factoid, message):
        if factoid["trigger"] == message.content:
            return True
        else:
            return False

    def substring_match(self, factoid, message):
        if factoid["trigger"] in message.content:
            return True
        else:
            return False

    def regex_match(self, factoid, message):
        if re.search(factoid["trigger"], message.content) is not None:
            return True
        else:
            return False

    # NEW SHIT HAS ENDED RIGHT HERE

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
            await self.check_factoid(message)
            await self.bandnames(message)

            first = message.content.split(' ')[0]

            if message.content in self.commands:
                await self.commands[message.content](message)

            elif first in self.commands:
                await self.commands[first](message)

            await self.goddamnit_eric(message)

        except Exception as inst:
            self.logger.error((type(inst)))
            self.logger.error(inst.args)
            self.logger.error(inst)
            await self.guru_meditation(message, inst.args)

    """ Active commands """

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
                if message.content.startswith("!getquote"):
                    await self.safe_send_message(
                        message.channel,
                        "I don't have any quotes from that user.")
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

    async def barequote(self, message):
        return
        """
        if len(message.mentions) != 1:
            return
        if len(message.content) == (len(message.mentions[0].id) + 4):
            await self.getquote(message)
        """

    async def goddamnit_eric(self, message):
        if message.author.id == "299208991765037066":
            chance = random.randint(1, 100)
            if chance == 1:
                await self.safe_send_message(message.channel, "goddamnit eric")

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
                    msg = '"{} {} {}" would be a good name for a band.'.format(
                        s[0], s[1], s[2])
                    await self.safe_send_message(message.channel, msg)
                    self.bands["good band names"].append(s)
                    self.band_chance = 30
                    return
                self.band_chance = self.band_chance - 1
                return

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


# open secrets file for API token and start the bot
with open("SECRETS.yaml", 'r') as filein:
    secrets = yaml.load(filein)
bot = BroBot()
bot.run(secrets["token"])


# make sure things get saved to file
@atexit.register
def save_stuff():
    bot.cleanup()
