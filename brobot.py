import random
import yaml
import praw
import zalgo
import asyncio
import requests
from bs4 import BeautifulSoup
import re
import googleimages
from brobot_errors import CantDoThatDave
from helper_functions import hf_dict


with open("data/SECRETS.yaml", "r") as filein:
    secrets = yaml.load(filein)

tumblr_api_key = secrets['tumblrapi']
reddit_id = secrets['redditid']
reddit_secret = secrets['redditsecret']


class BroBotCore:

    def __init__(self, discord_client, data_handler, logger):
        self.discord_client = discord_client
        self.logger = logger
        self.dh = data_handler
        self.fdb = self.dh.fdb
        self.qdb = self.dh.qdb
        self.bands = self.dh.bands
        self.guru_meditation = self.discord_client.guru_meditation
        self.miscdata = self.dh.miscdata
        self.madlib = self.miscdata["madlib"]
        self.reddit = praw.Reddit(client_id=reddit_id,
                                  client_secret=reddit_secret,
                                  user_agent="brobot")
        self.commands = {
                "!channel": self.whichchannel,
                "sfw sasuke": self.sasuke,
                "!brobot": self.add_factoid,
                "!addfactoid": self.add_factoid,
                "!brobotreact": self.add_factoid,
                "!addquote": self.addquote,
                "!getquote": self.getquote,
                "!manquote": self.manquote,
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
                "!wordsearch": self.add_factoid,
                "!zalgo": self.zalgo_text,
                "!lastfactoid": self.lastfactoid,
                "!deletefactoid": self.deletefactoid,
                "!searchfactoid": self.searchfactoid,
                "!findfactoid": self.findfactoid,
                "!retro": self.retro_text
                }

        # the starting chance that he
        # will mention something is a good band name
        self.band_chance = 80

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
        except CantDoThatDave as cdtd:
            await self.discord_client.safe_send_message(
                cdtd.d_message.channel, "I'm sorry but I can't do that Dave")

        except Exception as inst:
            self.logger.error((type(inst)))
            self.logger.error(inst.args)
            self.logger.error(inst)
            await self.guru_meditation(message, inst.args)

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
            if "$***" in msg_txt:
                # regex
                trigger, response = self.split_factoid(message.content,
                                                       "!wordsearch")
                trigger = self.prep_regex(trigger)
                await self.add_to_fdb(message, trigger, response,
                                      "regex", "text")
            else:
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
                trigger = "^" + re.escape(trigger) + "$"
                await self.add_to_fdb(message, trigger, response,
                                      "fullstring", "text")

    async def add_to_fdb(self, message, trigger, response,
                         trigger_type, response_type):
        f_id = self.miscdata["next_factoid_id"]
        factoid = {"trigger_type": trigger_type,
                   "response_type": response_type,
                   "trigger": trigger, "response": response,
                   "user": message.author.id, "factoid_id": f_id}

        self.fdb.append(factoid)
        self.miscdata["next_factoid_id"] += 1

        msg = "Okay {}, \"{}\" is \"{}\"".format(
            message.author.mention, trigger, response)
        await self.discord_client.safe_send_message(message.channel, msg)

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
        possible_responses = []

        for factoid in self.fdb:
            fut = self.reg_match(factoid["trigger"], message.content)
            try:
                regex_match = await asyncio.wait_for(fut, 5)
            except asyncio.TimeoutError:
                self.logger.error("Timed out, skipping")
                regex_match = None
                continue
            if regex_match is not None:
                # we include the match object in case we need any possible
                # match groups later
                possible_responses.append([factoid, regex_match])

        if len(possible_responses) >= 1:

            chosen_factoid = random.choice(possible_responses)
            response_txt = await self.response_parse(message, chosen_factoid)

            # send messages here
            await self.discord_client.safe_send_message(
                message.channel, response_txt)

    async def reg_match(self, trigger, msg_txt):
        match = re.search(trigger, msg_txt)
        return match

    # NEW SHIT HAS ENDED RIGHT HERE

    """ Utility functions """
    def is_me(self, message):
        return message.author == self.discord_client.user

    def add_to_swearjar(self):
        self.miscdata["swearjar"] += 25

    async def whichchannel(self, message):
        await self.discord_client.safe_send_message(
            message.channel, message.channel)

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

    """ Active commands """

    async def manquote(self, message):
        s = self.strip_command(message.content, "!manquote")
        if len(message.mentions) < 1:
            msg = "You need to mention a user to quote them."
            await self.discord_client.safe_send_message(message.channel, msg)
            return
        user_to_quote = message.mentions[0]
        user_quoting = message.author

        if user_to_quote.id not in self.qdb:
            self.qdb[user_to_quote.id] = {
                "name": user_to_quote.name,
                "discriminator": user_to_quote.discriminator,
                "quotes": []}
        quote = s.split(" ", 1)[1]
        quote_text = (quote
                      + "\n    - added manually by {}".format(
                          user_quoting.name))
        self.qdb[user_to_quote.id]["quotes"].append(quote_text)
        await self.discord_client.safe_send_message(
            message.channel, 'Manually quoted {} saying: "{}"'.format(
                user_to_quote.mention, quote))

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
                await self.discord_client.safe_send_message(
                    message.channel,
                    'Quoted {} saying: "{}"'.format(user.mention,
                                                    quotes[0].content))
            else:
                await self.discord_client.safe_send_message(
                    message.channel, "You'll have to be more specific")
                return

    async def getquote(self, message):
        """
        returns a random quote from a given user
        """
        for user in message.mentions:
            if user.id not in self.qdb:
                await self.discord_client.safe_send_message(
                    message.channel, "I don't have any quotes from that user.")
            quotes = self.qdb[user.id]["quotes"]
            if len(quotes) <= 0:
                if message.content.startswith("!getquote"):
                    await self.discord_client.safe_send_message(
                        message.channel,
                        "I don't have any quotes from that user.")
                return
            quote = random.choice(quotes)
            msg = '{} said:\n  {}'.format(user.mention, quote)
            await self.discord_client.safe_send_message(message.channel, msg)

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
        await self.discord_client.safe_send_message(message.channel, img_url)

    async def zalgo_text(self, message):
        text = message.content.split(" ", 1)[1]
        zalgo_text = zalgo.main(text, "NEAR")
        await self.discord_client.safe_send_message(
            message.channel, zalgo_text)

    async def madcats(self, message):
        """
        Lists current available madlib catergories
        """
        cats = [k for k, v in self.miscdata["madlib"].items()]
        s_cats = " ".join(cats)
        msg = "My current madlib categories are: {}".format(s_cats)
        await self.discord_client.safe_send_message(message.channel, msg)

    async def swearjar(self, message):
        dollas = float(self.miscdata["swearjar"]) / 100
        dollars = "${:,.2f}".format(dollas)
        msg = "There is {} in the swear jar".format(dollars)
        await self.discord_client.safe_send_message(message.channel, msg)

    async def addlib(self, message):
        """
        Adds a give word to a given madlib category with format
        '!addlib <category> <word>'
        """
        s = self.strip_command(message.content, "!addlib")
        s = s.split(" ", 1)
        if s[1] not in self.miscdata["madlib"]:
            await self.discord_client.safe_send_message(
                message.channel, "I'm sorry thats not a category.... yet")
            return
        else:
            self.miscdata["madlib"][s[1]].append(s[2])
            msg = "Okay {}, {} added to {}".format(
                message.author.mention, s[2], s[1])
            await self.discord_client.safe_send_message(message.channel, msg)

    async def addcat(self, message):
        """
        Adds a category to the madlib categories
        Currently will only allow me to do this
        """
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        else:
            cat = message.content.split(' ')[1]
            if cat[0] != "$":
                await self.discord_client.safe_send_message(
                    message.channel,
                    "The category should start with $")
                return
            if cat not in self.miscdata["madlib"]:
                self.miscdata["madlib"][cat] = []
                await self.discord_client.safe_send_message(
                    message.channel,
                    "{} madlib category added".format(cat))
            else:
                await self.discord_client.safe_send_message(
                    message.channel, "That category already exists")

    async def list_pockets(self, message):
        """"
        Lists what are in his poeckts
        """
        if len(self.miscdata["pockets"]) < 1:
            await self.discord_client.safe_send_message(
                message.channel, "My pockets are empty")
            return
        msg = "I have "
        for item in self.miscdata["pockets"]:
            msg = msg + "{} and ".format(item)
        msg = msg[:-5]
        await self.discord_client.safe_send_message(message.channel, msg)

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
            await self.discord_client.safe_send_message(message.channel, msg)
        else:
            self.miscdata["pockets"].append(item)
            msg = "Thanks for the {}, {}".format(item, message.author.mention)
            await self.discord_client.safe_send_message(message.channel, msg)

    async def empty_pockets(self, message):
        """
        Removes an item from his pockets at random and gives it to the person
        who asked
        """
        if len(self.miscdata["pockets"]) < 1:
            await self.discord_client.safe_send_message(
                message.channel, "My pockets seem to be empty")
            return
        item = random.choice(self.miscdata["pockets"])
        self.miscdata["pockets"].remove(item)
        msg = "Here {}, have a {}".format(message.author.mention, item)
        await self.discord_client.safe_send_message(message.channel, msg)

    async def sasuke(self, message):
        msg = await self.discord_client.safe_send_file(
            message.channel, 'images/SFWSASUKE.png')
        await self.safe_add_reaction(msg, "💯")
        await self.safe_add_reaction(msg, "😍")
        await self.safe_add_reaction(msg, "👌")

    async def silence_fillers(self, message):
        possible_thoughts = [submission.title for submission in
                             self.reddit.subreddit(
                                 "showerthoughts").hot(limit=30)
                             if submission.title
                             not in self.miscdata["silence_fillers"]]
        msg = random.choice(possible_thoughts)
        self.miscdata["silence_fillers"].append(msg)
        await self.discord_client.safe_send_message(message.channel, msg)

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
            await self.discord_client.safe_send_message(message.channel, msg)
            return
        meme = random.choice(pic_list)
        await self.discord_client.safe_send_message(message.channel, meme)

    """ Passive functions. Each message is passed to these to look for various
        conditions. Brobot may then respond. """

    async def lastfactoid(self, message):
        if message.author.id != "204378458393018368":
            return
        last_factoid = max(self.fdb, key=lambda x: x["factoid_id"])
        msg_txt = ("Factoid ID: {factoid_id}\n"
                   + "Trigger: {trigger}\n"
                   + "Response: {response}\n"
                   + "Author ID: {user}\n").format(**last_factoid)
        await self.discord_client.safe_send_message(message.channel, msg_txt)

    async def findfactoid(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        factoid_id = int(message.content.split(" ", 1)[1])
        find_factoid_list = [factoid for factoid in self.fdb
                             if factoid["factoid_id"] == factoid_id]
        if len(find_factoid_list) != 1:
            await self.discord_client.safe_send_message(
                message.channel, ("Either no match or too"
                                  + " many matches for that ID"))
            return
        find_factoid = find_factoid_list[0]
        msg_txt = ("Factoid ID: {factoid_id}\n"
                   + "Trigger: {trigger}\n"
                   + "Response: {response}\n"
                   + "Author ID: {user}\n").format(**find_factoid)
        await self.discord_client.safe_send_message(message.channel, msg_txt)

    async def searchfactoid(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        response_search_string = message.content.split(" ", 1)[1].strip()
        trigger_search_string = re.escape(response_search_string)

        found_factoids = [factoid for factoid in self.fdb
                          if response_search_string in factoid["response"]
                          or trigger_search_string in factoid["trigger"]]
        await self.discord_client.safe_send_message(
            message.channel, "I found the following factoids:")
        for factoid in found_factoids:
            msg_txt = ("Factoid ID: {factoid_id}\n"
                       + "Trigger: {trigger}\n"
                       + "Response: {response}\n"
                       + "Author ID: {user}\n").format(**factoid)

            await self.discord_client.safe_send_message(
                message.channel, msg_txt)

    async def deletefactoid(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        factoid_id = int(message.content.split(" ", 1)[1])
        find_factoid_list = [factoid for factoid in self.fdb
                             if factoid["factoid_id"] == factoid_id]
        if len(find_factoid_list) != 1:
            await self.discord_client.safe_send_message(
                message.channel, ("Either no match or too"
                                  + "many matches for that ID"))
            return
        find_factoid = find_factoid_list[0]
        msg_txt = ("Deleting this factoid:\n"
                   + "Factoid ID: {factoid_id}\n"
                   + "Trigger: {trigger}\n"
                   + "Response: {response}\n"
                   + "Author ID: {user}\n").format(**find_factoid)

        await self.discord_client.safe_send_message(message.channel, msg_txt)
        self.fdb.remove(find_factoid)

    async def goddamnit_eric(self, message):
        if message.author.id == "299208991765037066":
            chance = random.randint(1, 100)
            if chance == 1:
                await self.discord_client.safe_send_message(
                    message.channel, "goddamnit eric")

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
                    await self.discord_client.safe_send_message(
                        message.channel, msg)
                    self.bands["good band names"].append(s)
                    self.band_chance = 80
                    return
                self.band_chance = self.band_chance - 1
                return

    async def response_parse(self, message, chosen_factoid):
        """
            takes a chosen factoid and runs through any
            keywords in that factoid, returns the reponse
            plaintext to the check factoid function
        """
        # simple functions
        response_txt = chosen_factoid[0]["response"]
        match_obj = chosen_factoid[1]
        split_txt = response_txt.split()
        split_response = []
        for word in split_txt:
            # dealing with the corner case of italicized messages
            if word.startswith("*$"):
                word = word[1:]
                if word[-1] in ["!", ".", ",", "?", ";"]:
                    word = word[0:-1]
            if word in hf_dict:
                new_word = hf_dict[word](message)
            else:
                new_word = await self.madlibword(message, word, match_obj)
            if new_word is not None:
                split_response.append(new_word)

        return " ".join(split_response)

    async def madlibword(self, message, stringIn, reg_match_obj):

        """
        looks for madlib categories associated with the supplied word and swaps
        them out as necessary
        """
        # showerthoughts from reddit
        if stringIn.startswith("$thought"):
            await self.silence_fillers(message)
            return None
        # wildcard group matching
        if stringIn.startswith("$["):
            if not stringIn.endswith("]"):
                word_end = stringIn.split("]")[1]
            else:
                word_end = ""
            match_index = int(stringIn[2])
            return reg_match_obj.group(match_index) + word_end
        # madlib categories
        for k, v in self.madlib.items():
            if stringIn.startswith(k):
                return random.choice(v)
        else:
            return stringIn
