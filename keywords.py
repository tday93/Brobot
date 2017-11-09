import re
from random import choice, randint


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
        self.bot.logger.debug("Trying keyword: {}".format(self.name))
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
        print(key_matches)
        km_tuples = {(item, int(item[2:-1])) for item in key_matches}
        for item in km_tuples:
            response_txt = response_txt.replace(item[0], match_obj[item[1]])
        return response_txt


"""
def item(message, bot_instance=None):
    return random.choice(bot_instance.miscdata["pockets"])


def swearjar(message, bot_instance=None):
    return bot_instance.add_to_swearjar()
"""
