import discord
import asyncio
import subprocess
import botplugins
import urllib.request
import yaml
botresponses = botplugins.BotPlugins()
client =discord.Client()

@client.event
async def on_ready():
    print("logged in as")
    print(client.user.name)
    print(client.user.id)
    print('-------')

@client.event
async def on_message(message, num = 10):


    def is_me(m):
        return m.author == client.user

    if message.author == client.user:
        return

    if message.content.startswith("!delete"):
        num = int(message.content.split(' ')[1])
        await client.purge_from(message.channel, limit=num, check=is_me)
        return

    response = botresponses.get_response(message, client)
    if response != None:
        for r in response:
            if r != None:
                await rfuncs[r.rtype](r)

async def s_msg(r):
    print("SENDING FROM HERE")
    sent = await client.send_message(r.message.channel, r.content)
    return sent

async def s_file(r):
    sent = await client.send_file(r.message.channel, r.content)
    return sent

async def s_react(r):
    sent = await client.add_reaction(r.message, r.content)
    return sent

rfuncs = {'text':s_msg, 'file':s_file, 'react':s_react}

with open("SECRETS.yaml", 'r') as filein:
    secrets = yaml.load(filein)

client.run(secrets["token"])
