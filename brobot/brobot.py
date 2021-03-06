import random
import yaml
import praw
import zalgo
import asyncio
import requests
import re
import keywords as kw
from decimal import Decimal
from bs4 import BeautifulSoup
import helper_functions as hf
import googleimages
from brobot_errors import CantDoThatDave


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
        self.permissions = self.dh.permissions
        self.messages = []
        self.haiku = 0
        self.guru_meditation = self.discord_client.guru_meditation
        self.miscdata = self.dh.miscdata
        self.madlib = self.miscdata["madlib"]
        self.reddit = praw.Reddit(client_id=reddit_id,
                                  client_secret=reddit_secret,
                                  user_agent="brobot")
        self.keywords = self.get_keywords()
        self.commands = {
                "!ignore": self.global_ignore,
                "!unignore": self.global_unignore,
                "!help": self.get_help,
                "!channel": self.whichchannel,
                "sfw sasuke": self.sasuke,
                "!removepermission": self.remove_permission,
                "!triggerchance": self.update_factoid_trigger,
                "!inspect": self.inspect,
                "!syllables": self.check_syllables,
                "!addpermission": self.add_permission,
                "!brobot": self.add_factoid,
                "!addfactoid": self.add_factoid,
                "!brobotreact": self.add_factoid,
                "!addquote": self.addquote,
                "!allquote": self.allquote,
                "!getquote": self.getquote,
                "!manquote": self.manquote,
                "!memeplease": self.memeplease,
                "!shop": self.buy_item,
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
        self.response_cache = {}

        # the starting chance that he
        # will mention something is a good band name
        self.band_chance = 80
        self.response_chance_padding = 0
        self.ignored_users = []

    async def get_help(self, message):
        """ !help [command]:
            Used to get help about how to use another command.
        """
        try:
            command = message.content.split(" ", 1)[1]
            self.logger.info("Command help: {}".format(command))
            func_help = str(self.commands[command].__doc__)
            self.logger.info("{}".format(func_help))
            await self.discord_client.safe_send_message(message.channel, func_help)
        except KeyError:
            await self.discord_client.safe_send_message(message.channel, "No command by that name")
        except IndexError:
            await self.discord_client.safe_send_message(message.channel, self.get_help.__doc__)
        except Exception as e:
            raise e

    async def get_response(self, message):

        """
        Core routing function.
            0. Checks if user should be globally ignored.
            1. checks for band name
            2. checks for commands
                a. if command is present, strips invocation and sends to
                    appropriate function
            3. checks for regex matches
            4. checks for factoids
            5. checks if user should be locally ignored.
        """
        try:
            if message.author.id in self.ignored_users:
                self.logger.debug(f"Ignoring message from {message.author.username}")
            if message.author.id not in self.ignored_users:
                await self.check_haiku(message)
                await self.check_factoid(message)
                await self.bandnames(message)

            first = message.content.split(' ')[0]

            if message.content in self.commands:
                if await self.permissions_check(message.content,
                                                message.author.id, message):
                    await self.commands[message.content](message)

            elif first in self.commands:
                if await self.permissions_check(first, message.author.id,
                                                message):
                    await self.commands[first](message)

            await self.goddamnit_eric(message)
            self.messages.append(message)
        except CantDoThatDave as cdtd:
            await self.discord_client.safe_send_message(
                cdtd.d_message.channel, "I'm sorry but I can't do that Dave")

        except Exception as inst:
            self.logger.error((type(inst)))
            self.logger.error(inst.args)
            self.logger.error(inst)
            await self.guru_meditation(message, inst.args)

    async def inspect(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        else:
            var = message.content.split(" ", 1)[1]
            try:
                msg = repr(getattr(self, var))
                if len(msg) > 32:
                    msg = "Value too long to send"
                await self.discord_client.safe_send_message(message.channel, msg)
            except:
                return

    async def global_ignore(self, message):
        """
            Make brobot ignore particular users.
            @ every user you'd like him to ignore
        """
        if not self.is_mod(message.author):
            raise CantDoThatDave(message)
        try:
            users_to_ignore = message.mentions
            for user in users_to_ignore:
                self.ignored_users.append(user.id)
        except IndexError:
            await self.discord_client.safe_send_message(message.channel, "No user selected")

    async def global_unignore(self, message):
        """
            Make brobot unignore particular users.
            @ every user you'd like him to unignore
        """
        if not self.is_mod(message.author):
            raise CantDoThatDave(message)
        try:
            users_to_unignore = [user.id for user in message.mentions]
            self.ignored_users = [user for user in self.ignored_users if user not in users_to_unignore]

        except IndexError:
            await self.discord_client.safe_send_message(message.channel, "No user selected")

    async def check_haiku(self, message):

            syls = hf.syllable_count(message.content)
            if syls == 5:
                if self.haiku == 0:
                    self.haiku == 1
                    self.logger.info("First haiku line")
                    return
                elif self.haiku == 2:
                    await self.discord_client.safe_send_message(message.channel, "A Haiku!")
                    self.haiku = 0
                    return
                else:
                    self.haiku = 0
            elif syls == 7:
                self.logger.info("Seven syllables!, self.haiku={}".format(self.haiku))
                if self.haiku == 1:
                    self.haiku = 2
                    self.logger.info("Second haiku line!")
                    return
                else:
                    self.haiku = 0
            else:
                self.logger.info("Syls = {}, haiku cleared".format(syls))
                self.haiku = 0

    async def check_syllables(self, message):
        """ !syllables [word or phrase]:
            Tells you how many syllables brobot thinks are in a given word or phrase
        """
        txt = message.content.split(" ", 1)[1]
        syls = hf.syllable_count(txt)
        msg = "There are {} syllables in that phrase".format(syls)
        await self.discord_client.safe_send_message(message.channel, msg)

    async def handle_reaction(self, reaction, user):
        self.logger.error("Recieved reaction: {}".format(reaction.emoji))
        self.logger.info("message id: {}".format(reaction.message.id))
        if reaction.message.id in self.response_cache:
            f_id = self.response_cache[reaction.message.id]
            self.logger.info("Factoid ID: {}".format(f_id))
            if str(reaction.emoji) == "👍":
                self.logger.info("Thumbs up")
                await self.factoid_chance(f_id, 1)
            elif str(reaction.emoji) == "👎":
                self.logger.info("Thumbs down")
                await self.factoid_chance(f_id, -5)
        return

    async def factoid_chance(self, factoid_id, chance_delta):
        self.logger.info("Factoid ID: {}".format(factoid_id))
        self.logger.info("chance delta: {}".format(chance_delta))
        factoid = [f for f in self.fdb if f["factoid_id"] == factoid_id][0]
        self.logger.info("Factoid: {}".format(factoid))
        new_trigger_chance = factoid["trigger_chance"] + chance_delta
        self.logger.info("new trigger chance = {}".format(new_trigger_chance))
        if new_trigger_chance < 0:
            new_trigger_chance = 0
        elif new_trigger_chance > 100:
            new_trigger_chance = 100
        factoid["trigger_chance"] = new_trigger_chance

    async def permissions_check(self, cmd_trigger, userid, message):
        if userid in self.permissions:
            if cmd_trigger in self.permissions[userid]["blacklist"]:
                raise CantDoThatDave(message)
            else:
                return True
        else:
            self.permissions[userid] = {"whitelist": [], "blacklist": []}
            return True

    async def remove_permission(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        else:
            user = message.mentions[0]
            if user.id not in self.permissions:
                self.permissions[user.id] = {"whitelist": [], "blacklist": []}
            cmd = message.content.split()[2]
            self.permissions[user.id]["blacklist"].append(cmd)

    async def add_permission(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        else:
            user = message.mentions[0]
            if user.id not in self.permissions:
                self.permissions[user.id] = {"whitelist": [], "blacklist": []}
            cmd = message.content.split()[2]
            if cmd in self.permissions[user.id]["blacklist"]:
                self.permissions[user.id]["blacklist"].remove(cmd)

    async def add_factoid(self, message):
        """ (!brobot | !addregex | !wordsearch) [trigger] <is> [response] {%%(10-100)}:
            Teaches brobot a response to a given trigger.
            \"!brobot\" will force the trigger to match the entire messge.
            \"!addregex\" will interpret the trigger as regex to use to test matches.
            \"!wordsearch\" will look for the trigger anywhere in the message

            Trigger chance:
                You can assign the factoid a chance to fire with "%%(10-100)"
                This chance can be altered by server voting, but will never drop below 10%

            You can include keywords in your reponse that will do different things. The below
            are those that are implemented currently:

            Keywords:
                $digit: random digit 0-9
                $nonzero: random digit 1-9
                $someone: the nickname of a random person on the server
                $who: the nickname of whoever trigger the factoid
                $item: a random item from brobots inventory
                $bible: A fake bible quote
                $swearjar: this will cause a quarter to be added to the swearjar
                $thought: Brobot will replace this with what hes thinking about
                $compliment: a simple randomly generated compliment
        """
        msg_txt = message.content
        trigger_chance = 100
        try:
            t_chance = int(re.search("\%\%([0-9][0-9])", msg_txt).group(1))
            if t_chance is not None:
                msg_txt = re.sub("\%\%([0-9][0-9])", "", msg_txt)
                trigger_chance = t_chance
        except:
            pass

        # determine factoid type
        if msg_txt.startswith("!addregex"):
            # user_regex
            trigger, response = self.split_factoid(msg_txt,
                                                   "!addregex")
            await self.add_to_fdb(message, trigger, response,
                                  "regex", "text", trigger_chance=trigger_chance)

        elif msg_txt.startswith("!wordsearch"):
            # substring
            # prepare factoid data
            trigger, response = self.split_factoid(msg_txt,
                                                   "!wordsearch")
            if "$***" in msg_txt:
                # regex
                trigger, response = self.split_factoid(
                    message.content.casefold(), "!wordsearch")
                trigger = self.prep_regex(trigger)
                await self.add_to_fdb(message, trigger, response,
                                      "regex", "text", trigger_chance=trigger_chance)
            else:
                await self.add_to_fdb(message, trigger, response,
                                      "substring", "text", trigger_chance=trigger_chance)

        elif msg_txt.startswith("!addreaction"):
            # reactions
            trigger, response = self.split_factoid(msg_txt,
                                                   "!addreaction")
            await self.add_to_fdb(message, trigger, response,
                                  "substring", "reaction", trigger_chance=trigger_chance)

        elif msg_txt.startswith("!addregex"):
            # user_regex
            trigger, response = self.split_factoid(msg_txt,
                                                   "!addregex")
            await self.add_to_fdb(message, trigger, response,
                                  "regex", "text", trigger_chance=trigger_chance)
        elif msg_txt.startswith("!brobot"):
            # either fullstring or regex
            if "$***" in msg_txt:
                # regex
                trigger, response = self.split_factoid(
                    msg_txt, "!brobot")
                trigger = self.prep_regex(trigger)
                await self.add_to_fdb(message, trigger, response,
                                      "regex", "text", trigger_chance=trigger_chance)
            else:
                # fulltext
                trigger, response = self.split_factoid(msg_txt,
                                                       "!brobot")
                trigger = "^" + re.escape(trigger) + "$"
                await self.add_to_fdb(message, trigger, response,
                                      "fullstring", "text", trigger_chance=trigger_chance)

    async def add_to_fdb(self, message, trigger, response,
                         trigger_type, response_type, trigger_chance=100):
        f_id = self.miscdata["next_factoid_id"]
        factoid = {"trigger_type": trigger_type,
                   "trigger_chance": trigger_chance,
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
            trigger = t[0].strip()
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

            # select if factoid will be displayed based on weighting
            n = random.randrange(0, 100) - self.response_chance_padding
            final_factoids = [r for r in possible_responses
                              if r[0]["trigger_chance"] >= n]
            if len(final_factoids) <= 0:
                self.response_chance_padding += 5
            elif len(final_factoids) >= 1:
                self.response_chance_padding = 0
                # choose factoid to be displayed
                c_factoid = random.choice(final_factoids)
                response_txt = await self.better_parse(message, c_factoid)

                # send messages here
                msg = await self.discord_client.safe_send_message(
                    message.channel, response_txt)
                self.logger.info("adding to cache: {}, {}".format(
                    msg.id, c_factoid[0]["factoid_id"]))
                self.response_cache[msg.id] = c_factoid[0]["factoid_id"]

    async def reg_match(self, trigger, msg_txt):
        match = re.search(trigger, msg_txt)
        return match

    # NEW SHIT HAS ENDED RIGHT HERE

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
        """ !addquote [@user] [message snippet]
            Adds a quote from the @ed user.
            Message snippet must be exact.
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
        """ !getquote [@user] (?={search string})
            Returns a random quote from the @ed user. Can optionally search for a quote
            matching the given string.
        """
        for user in message.mentions:
            if user.id not in self.qdb:
                await self.discord_client.safe_send_message(
                    message.channel, "I don't have any quotes from that user.")
            quotes = self.qdb[user.id]["quotes"]
            if "?=" in message.content:
                query = message.content.split("?=", 1)[1]
                quotes = [quote for quote in quotes if re.search(query, quote) is not None]
            if len(quotes) <= 0:
                if message.content.startswith("!getquote"):
                    await self.discord_client.safe_send_message(
                        message.channel,
                        "I don't have any matching quotes from that user.")
                return
            quote = random.choice(quotes)
            msg = '{} said:\n  {}'.format(user.mention, quote)
            await self.discord_client.safe_send_message(message.channel, msg)

    async def allquote(self, message):
        """
            !allquote [@user]
            Prints all quotes from a given user, only usable by tday.
        """
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        for user in message.mentions:
            if user.id not in self.qdb:
                await self.discord_client.safe_send_message(
                    message.channel, "I don't have any quotes from that user.")
            quotes = self.qdb[user.id]["quotes"]
            if "?=" in message.content:
                query = message.content.split("?=", 1)[1]
                quotes = [quote for quote in quotes if re.search(query, quote) is not None]
            if len(quotes) <= 0:
                if message.content.startswith("!getquote"):
                    await self.discord_client.safe_send_message(
                        message.channel,
                        "I don't have any matching quotes from that user.")
                return
            for quote in quotes:
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
        """ !zalgo [phrase]:
            returns the phrase zalgo'd
        """
        text = message.content.split(" ", 1)[1]
        zalgo_text = zalgo.main(text, "NEAR")
        await self.discord_client.safe_send_message(
            message.channel, zalgo_text)

    async def buy_item(self, message):
        """ !shop:
            Searches craigslist for an item brobot can afford and "buys" it with money from his swearjar
        """
        budget = self.miscdata["swearjar"]
        item = await self.find_from_craigslist(budget)
        if item is not None:
            self.miscdata["swearjar"] -= item["price"]
            if self.miscdata["swearjar"] < 0:
                self.miscdata["swearjar"] = 0
            if len(self.miscdata["pockets"]) >= 5:
                discarded = self.miscdata["pockets"].pop(0)
                self.miscdata["pockets"].append(item["name"])
                msg = "Okay {}, I threw out my {} and bought {}, from {}".format(
                    message.author.mention, discarded, item["name"], item["link"])
                await self.discord_client.safe_send_message(message.channel, msg)
            else:
                self.miscdata["pockets"].append(item)
                msg = "I bought {} from {}".format(item["name"], item["price"])
                await self.discord_client.safe_send_message(message.channel, msg)
        else:
            msg = "I couldn't find anything I could afford"
            await self.discord_client.safe_send_message(message.channel, msg)

    async def find_from_craigslist(self, budget):
        r = requests.get("https://losangeles.craigslist.org/d/for-sale/search/sss")
        print(r.status_code)
        soup = BeautifulSoup(r.content, "html5lib")
        all_items = soup.findAll("li", "result-row")
        items_formatted = []
        for item in all_items:
            price = None
            prices = item.findAll("span", "result-price")
            if prices:
                price = str(prices[0].contents)
                value = Decimal(re.sub(r'[^\d.]', '', price)) * 100
                if value < budget:
                    f_item = {
                        "name": item.p.a.contents,
                        "price": value,
                        "link": item.a["href"]
                    }
                    items_formatted.append(f_item)

        return random.choice(items_formatted)

    async def madcats(self, message):
        """ !categories:
            Lists brobot's current wildcard categories
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
        """ !addlib [category] [word]:
            Adds [word] to brobots wildcard category [category]
            Categories can be listed with \"!categories\"
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
        """!addcat [category]
            Adds a wilcard category to brobots list of categories.
            Currently only enabled for tday.
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
        """!pockets:
            Lists the items in brobot's inventory
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
        """!give [item]:
            Gives [item] to brobot to keep in his inventory, will drop and item if he is already at his cap
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
        """!take:
            Chooses a random item from his inventory and gives it to the person who asked for it.
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
        await self.discord_client.safe_add_reaction(msg, "💯")
        await self.discord_client.safe_add_reaction(msg, "😍")
        await self.discord_client.safe_add_reaction(msg, "👌")

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
        """!memeplease [tag]:
            Looks for images on tumblr with the given tag, and posts one randomly.
            Note that it is only looking for a single tag.
            i.e. \"!memplease hot dog\" will look for images tagged with \"hot dog\", not both \"hot\" and \"dog\"
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
                   + "Trigger Chance: {trigger_chance}\n"
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
                       + "Trigger Chance: {trigger_chance}\n"
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
                   + "Trigger Chance: {trigger_chance}\n"
                   + "Author ID: {user}\n").format(**find_factoid)

        await self.discord_client.safe_send_message(message.channel, msg_txt)
        self.fdb.remove(find_factoid)

    async def update_factoid_trigger(self, message):
        if message.author.id != "204378458393018368":
            raise CantDoThatDave(message)
        try:
            rr = re.search("!triggerchance id=(\d*) \%\%(\d*)", message.content)
            factoid_id = int(rr.group(1))
            trigger_chance = int(rr.group(2))
            factoid = [factoid for factoid in self.fdb if factoid["factoid_id"] == factoid_id][0]
            factoid["trigger_chance"] = trigger_chance

            msg = "Updated factoid {} to have trigger chance {}".format(factoid_id, trigger_chance)
            await self.discord_client.safe_send_message(message.channel, msg)
        except IndexError:
            await self.discord_client.safe_send_message(message.channel, "No factoid with that ID")
        except Exception as e:
            raise e

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

    def get_keywords(self):
        # special keywords firs
        key_objs = [
            kw.Digit(self, "$digit"),
            kw.NonZero(self, "$nonzero"),
            kw.Someone(self, "$someone"),
            kw.Who(self, "$who"),
            kw.Item(self, "$item"),
            kw.FakeBible(self, "$bible"),
            kw.Swearjar(self, "$swearjar"),
            kw.Thought(self, "$thought"),
            kw.Wildcard(self, "$wildcard"),
            kw.Compliment(self, "$compliment")
        ]
        for key in self.madlib:
            key_objs.append(kw.Keyword(self, key))
        return key_objs

    async def better_parse(self, message, chosen_factoid):
        response_txt = chosen_factoid[0]["response"]
        match_obj = chosen_factoid[1]
        for keyword in self.keywords:
            if keyword.match(response_txt):
                self.logger.debug("Match for {}".format(keyword.name))
                response_txt = await keyword.transform(response_txt,
                                                       message, match_obj)
                self.logger.debug(response_txt)
        return response_txt

    def is_mod(self, user):
        user_roles = [role.name for role in user.roles]
        print(user_roles)
        for role in ["prok", "crunchwrap supreme", "frost", "thotties"]:
            if role in user_roles:
                return True
        return False
