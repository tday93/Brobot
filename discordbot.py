import discord
import asyncio
import subprocess
import botplugins
import urllib.request
import yaml
import atexit
br = botplugins.BotPlugins


class BroBot(discord.Client, br):


    def __init__(self):
        self.fdb = self.getjson("factoids.json")
        self.qdb = self.getjson("quotes.json")
        self.rdb = self.getjson("reactions.json")
        self.bands = self.getjson("bands.json")
        self.miscdata = self.getjson("miscdata.json")
        br.__init__(self)
        super().__init__()

    def cleanup(self):
        print("cleaning up")
        self.writejson("factoids.json", self.fdb)
        self.writejson("reactions.json", self.rdb)
        self.writejson("quotes.json", self.qdb)
        self.writejson("bands.json", self.bands)
        self.writejson("miscdata.json", self.miscdata)

    async def on_ready(self):
        print("logged in as")
        print(self.user.name)
        print(self.user.id)
        print('-------')

    async def on_message(self,message, num = 10):

        print(message.content)
        if message.author == self.user:
            return

        await self.get_response(message)


    async def safe_send_message(self, dest, content):
        msg = None
        try:
            msg = await self.send_message(dest, content)
            return msg
        except:
            print("nope")


    async def safe_send_file(self, dest, content):
        msg = None
        try:
            msg = await self.send_file(dest, content)
            return msg
        except:
            print("Nada")

    async def safe_add_reaction(self, message, content):
        try:
            msg = await self.add_reaction(message, content)
            return msg
        except:
            print("no way")


with open("SECRETS.yaml", 'r') as filein:
    secrets = yaml.load(filein)
bot = BroBot()
bot.run(secrets["token"])

@atexit.register
def save_stuff():
    bot.cleanup()


