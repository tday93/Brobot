import random
import json


def digit(message, bot_instance=None):
    return str(random.randrange(0, 9))


def nonzero(message, bot_instance=None):
    return str(random.randrange(1, 9))


def someone(message, bot_instance=None):
    return random.choice(list(message.server.members)).mention


def item(message, bot_instance=None):
    return random.choice(bot_instance.miscdata["pockets"])


def who(message, bot_instance=None):
    return message.author.nick or message.author.name


def swearjar(message, bot_instance=None):
    return bot_instance.add_to_swearjar()


def fork_it_up(message):
    swaps = [("fuck", "fork"), ("shit", "shirt"), ("ass", "ash")]
    for item in swaps:
        if item[0] in message:
            message.replace(item[0], item[1])
    return message


def writejson(path, jd):
    with open(path, 'w') as outfile:
        json.dump(jd, outfile, indent=2,
                  sort_keys=True, separators=(',', ':'))


def getjson(path):
    with open(path) as fn:
        jd = json.load(fn)
    return jd


hf_dict = {
        "$digit": digit,
        "$nonzero": nonzero,
        "$someone": someone,
        "$item": item,
        "$who": who,
        "$swearjar": swearjar
}
