import subprocess
import os
import random
import requests
import urllib
import datetime
import json
import string
import re
from bhelpers import BResponse
import yaml

command_aliases ={
        "whichchannel":['!whichchannel'],
        "scotty":['butter me up scotty'],
        "smut":['!smut'],
        "butter":['pass me the butter'],
        "factoidinput":['!brobot'],
        "sasuke":['sfw sasuke'],
        "memeplease":['memeplease'],
        "reactioninput":["!brobotreact"],
        "adddjbrobot":["!add"],
        "getquote":['!getquote']
        }

with open("SECRETS.yaml", "r") as filein:
    secrets = yaml.load(filein)

tumblr_api_key = secrets['tumblrapi']

def makeRegistrar():
    registry = {}
    def registrar(func):
        registry[func.__name__] = func
        return func
    registrar.all = registry
    return registrar

reg = makeRegistrar()

@reg
def whichchannel( message):
    msg = message.channel
    print(msg)
    return BResponse('text', message, msg)

@reg
def adddjbrobot(message):
    mods = ["cucksquad", "crunchwrap supreme", "prok"]
    roles = []
    for role in message.author.roles:
        roles.append(role.name)
    print(roles)
    print(message.content)
    if  len(set(roles).intersection(mods)) <1 :
        return BResponse("text", message, "I can't let you do that dave")
    link = message.content.split(' ')[1]
    with open("DJBROBOT/MusicBot/config/autoplaylist.txt","a") as f:
        f.write(link +"\n")

@reg
def agree(message):
    msg = 'right {0.author.mention}'.format(message)
    return BResponse('text', message,msg)

@reg
def smut(message):
    if str(message.channel) =="general":
        return BResponse('text', message, "Not in here buddy.")

    msg = subprocess.run(['python', '/home/tday/projects/chatbots/markov.py'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    return BResponse('text',message, msg)

@reg
def scotty(message):
    r = requests.get('https://api.tumblr.com/v2/tagged?tag=scotty&api_key={0}'.format(tumblr_api_key))
    scottydict = r.json()
    pic_list=[]
    for item in scottydict['response']:
        if item['type'] == 'photo':
            for pic in item['photos']:
                if 'original_size' in pic:
                    pic_list.append(pic['original_size']['url'])


    scotty = random.choice(pic_list)
    return BResponse('text',message ,scotty)


@reg
def memeplease(message):
    tag = message.content.split(' ',1)[1]
    r = requests.get('https://api.tumblr.com/v2/tagged?tag={}&api_key={}'.format(tag, tumblr_api_key))
    memedict = r.json()
    pic_list=[]
    for item in memedict['response']:
        if item['type'] == 'photo':
            for pic in item['photos']:
                if 'original_size' in pic:
                    pic_list.append(pic['original_size']['url'])

    meme = random.choice(pic_list)
    return BResponse('text',message,meme)

@reg
def butter(message):
    return BResponse('file', message, 'butter.jpg')

@reg
def sasuke(message):
    return BResponse('file', message, 'SFWSASUKE.png')

def addquote(message, client):
    if len(message.mentions) != 1:
        return BResponse('text', message, 'I can only quote one user at once')
    user = message.mentions[0]
    qdb = getjson('quotes.json')
    if user.id not in qdb:
        qdb[user.id] = {"name":user.name, "discriminator":user.discriminator, "quotes": []}
    query = message.content.split(' ', 2)[2]
    quotes = []
    for message in client.messages:
        if message.author.id == user.id and message.content.startswith(query):
            quotes.append(message)
    if len(quotes) != 1:
        return BResponse('text', message, "You'll have to be more specific")
    qdb[user.id]["quotes"].append(quotes[0].content)
    writejson('quotes.json', qdb)
    return BResponse('text', message, 'Quoted {} saying: "{}"'.format(user.mention, quotes[0].content))



@reg
def getquote(message):
    qdb = getjson('quotes.json')
    if len(message.mentions) != 1:
        return BResponse('text', message, "I can only retrieve quotes from one user at a time")
    user = message.mentions[0]
    if user.id not in qdb:
        return BResponse('text', message, "I don't have any quotes from that user.")
    quotes = qdb[user.id]["quotes"]
    quote = random.choice(quotes)
    msg = '{} said: "{}"'.format(user.mention,quote)
    r = BResponse('text', message, msg)
    return r

@reg
def factoidinput(message):

    if os.path.isfile('factoids.json'):
        fdb = getjson('factoids.json')

    t = message.content.split(' ', 1)[1].split("<is>")
    trigger = t[0].strip()
    factoid = t[1].strip()
    if len(trigger) <1 or len(factoid) <1:
        return BResponse("text", message, "I dont understand that")

    if trigger in fdb:
        existing = fdb[trigger]
        if type(existing) is str:
            l = [existing, factoid]
            fdb[trigger] = l

        else:
            fdb[trigger].append(factoid)
    else:
        fdb[trigger] = []
        fdb[trigger].append(factoid)
    writejson('factoids.json', fdb)
    return None

def getfactoid(message):
    fdb = getjson('factoids.json')
    t = message.content
    if t in fdb:
        r = random.choice(fdb[t])
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
        return BResponse("text", message, r)
    return None



@reg
def reactioninput(message):
    mods = ["cucksquad", "crunchwrap supreme", "prok"]
    roles = []
    for role in message.author.roles:
        roles.append(role.name)
    if  len(set(roles).intersection(mods)) <1 :
        return BResponse("text",message, "I can't let you do that dave")

    if os.path.isfile('reactions.json'):
        fdb = getjson('reactions.json')
    t = message.content.split(' ', 1)[1]

    tl = t.split('<is>')
    print(tl)
    if len(tl) != 2:
        return BResponse("text", message, "Something went wrong.")

    trigger = tl[0].strip()
    factoid = tl[1].strip()

    if trigger in fdb:
        existing = fdb[trigger]
        if type(existing) is str:
            l = [existing, factoid]
            fdb[trigger] = l

        else:
            fdb[trigger].append(factoid)
    else:
        fdb[trigger] = []
        fdb[trigger].append(factoid)
    writejson('reactions.json', fdb)
    return None

def getreaction(message):
    print(message)
    fdb = getjson('reactions.json')
    t = message.content
    if t in fdb:
        return BResponse('react', message,random.choice(fdb[t]))
    return None

def writejson(path, jd):
    with open(path, 'w') as outfile:
        json.dump(jd, outfile, indent=2, sort_keys=True, separators=(',',':'))

def getjson(path):
    with open(path) as fn:
        jd = json.load(fn)
    return jd

class BotPlugins(object):

    def __init__(self):
        self.reg = reg.all

        self.commands = {}

        for k,v in command_aliases.items():
            for item in v:
                self.commands[item] = self.reg[k]

    def get_response(self,message, client):
        response = []
        trigger = message.content

        if message.content.startswith("!addquote"):
            response.append(addquote(message, client))

        if trigger in self.commands:
            response.append(self.commands[trigger](message))
            print(trigger.split(' ')[0])
        elif trigger.split(' ')[0] in self.commands:
            print("going to " + trigger.split(' ')[0])
            response.append(self.commands[trigger.split(' ')[0]](message))

        factoid = getfactoid(message)
        reaction = getreaction(message)
        if factoid != None:
            response.append(factoid)
        if reaction != None:
            response.append(reaction)

        print(response)


        return response


