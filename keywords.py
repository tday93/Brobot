import re
import markovify
from random import choice, randint
from book_names import name_chain


class Keyword:

    def __init__(self, bot, name, pattern=None, wordbucket=None):
        self.bot = bot
        self.name = name
        self.pattern = pattern or re.escape(self.name)
        self.word_bucket = wordbucket or self.name

    async def transform(self, response_txt, message, match_obj):
        new_word = choice(self.bot.madlib[self.word_bucket])
        return re.sub(self.pattern, new_word, response_txt)

    def match(self, response_txt):
        self.bot.logger.debug("Trying pattern: {}".format(self.pattern))
        if re.search(self.pattern, response_txt) is not None:
            return True
        else:
            return False


class Digit(Keyword):

    async def transform(self, response_txt, message, match_obj):
        new_word = str(randint(0, 9))
        return re.sub(self.pattern, new_word, response_txt)


class NonZero(Keyword):

    async def transform(self, response_txt, message, match_obj):
        new_word = str(randint(1, 9))
        return re.sub(self.pattern, new_word, response_txt)


class Someone(Keyword):

    async def transform(self, response_txt, message, match_obj):
        new_word = choice(list(message.server.members)).mention
        return re.sub(self.pattern, new_word, response_txt)


class Who(Keyword):

    async def transform(self, response_txt, message, match_obj):
        new_word = message.author.nick or message.author.name
        return re.sub(self.pattern, new_word, response_txt)


class Swearjar(Keyword):

    async def transform(self, response_txt, message, match_obj):
        response_txt = response_txt.replace(self.name, "")
        self.bot.add_to_swearjar()
        return response_txt


class FakeBible(Keyword):

    def __init__(self, bot, name, pattern=None, wordbucket=None):
        self.bible_model = get_markov_model("bible.txt")
        super().__init__(bot, name, pattern=pattern, wordbucket=wordbucket)

    async def transform(self, response_txt, message, match_obj):
        response_txt = await self.bible_verse()
        return response_txt

    async def bible_verse(self):
        raw_verse = self.bible_model.make_sentence().split(" ", 1)
        chap_verse = raw_verse[0].split(":")
        verse_text = re.sub("\\d+:\\d+", "", raw_verse[1])
        book = "".join(name_chain.walk()).capitalize()
        msg = 'From the book of {}, Chapter {}, Verse {}: \n"{}"'.format(
            book, chap_verse[0], chap_verse[1], verse_text)
        return msg


class Thought(Keyword):

    async def transform(self, response_txt, message, match_obj):
        possible_thoughts = [submission.title for submission in
                             self.bot.reddit.subreddit(
                                 "showerthoughts").hot(limit=30)
                             if submission.title
                             not in self.bot.miscdata["silence_fillers"]]
        new_word = choice(possible_thoughts)
        self.bot.miscdata["silence_fillers"].append(new_word)
        return re.sub(self.pattern, new_word, response_txt)


class Wildcard(Keyword):

    def __init__(self, bot, name, pattern=None, wordbucket=None):
        self.bot = bot
        self.name = name
        self.pattern = "(\$\[\d+\])"
        self.word_bucket = wordbucket or self.name

    async def transform(self, response_txt, message, match_obj):
        key_matches = re.findall(self.pattern, response_txt)
        self.bot.logger.debug("{}".format(key_matches))
        km_tuples = {(item, int(item[2:-1])) for item in key_matches}
        for item in km_tuples:
            self.bot.logger.debug("{}".format(item))
            new_word = ""
            try:
                self.bot.logger.debug("IN TRY BLOCK")
                new_word = match_obj.group(item[1])
                response_txt = response_txt.replace(item[0], new_word)
            except TypeError:
                self.bot.logger.debug("IN EXCEPTION")
                new_word = ""
                response_txt = response_txt.replace(item[0], new_word)
        return response_txt


class Item(Keyword):

    async def transform(self, response_txt, message, match_obj):
        item = choice(self.bot.miscdata["pockets"])
        return re.sub(self.pattern, item, response_txt)


class Compliment(Keyword):

    def __init__(self, bot, name, pattern=None, wordbucket=None):
        self.nouns = [
            "shirt",
            "hair",
            "legs",
            "breath",
            "pants",
            "shoes",
            "eyes",
            "ears",
            "voice",
            "jacket",
            "glasses",
            "bicep",
            "calf",
            "tricep",
            "undercarriage",
            "sprocket",
            "flange",
            "widget",
            "word"]
        self.verbs = [
            "looks",
            "smells",
            "tastes",
            "appears",
            "seems",
            "is"]
        self.adj = [
            "nice",
            "pretty",
            "beautiful",
            "shiny",
            "smooth",
            "playful",
            "powerful",
            "majestic",
            "mysterious",
            "angry",
            "fierce",
            "wrathful",
            "wholesome",
            "glorious",
            "statuesque",
            "hilarious",
            "human",
            "not at all robotic",
            "alive",
            "deadly",
            "crisp",
            "gorgeous",
            "balanced"]
        super().__init__(bot, name, pattern=pattern, wordbucket=wordbucket)

    async def transform(self, response_txt, message, match_obj):
        cn = choice(self.nouns)
        cv = choice(self.verbs)
        ca = choice(self.adj)
        new_word = "Your {} {} {} today!".format(cn, cv, ca)

        return re.sub(self.pattern, new_word, response_txt)


def get_markov_model(path):
    with open(path) as f:
        text = f.read()

    text_model = markovify.Text(text)
    return text_model
