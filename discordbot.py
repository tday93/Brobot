#!/usr/bin/python
import discord
import argparse
import logging
import random
import yaml
import atexit
import asyncio
from signal import SIGINT, SIGTERM, SIGABRT
import time
import sys
import zalgo
from data.data_handlers import DataHandler
import helper_functions
from brobot import BroBotCore


class BroBotClient(discord.Client):

    def __init__(self, data_handler):
        self.logger = logging.getLogger("brobotlog")
        self.brobot_core = BroBotCore(self, data_handler, self.logger)
        super().__init__()

    async def on_ready(self):
        self.logger.info("logged in as")
        self.logger.info(self.user.name)
        self.logger.info(self.user.id)
        self.logger.info('-------')

    async def on_message(self, message, num=10):

        if message.author == self.user:
            return
        self.logger.info("Received message: '{}'".format(message.content))
        await self.brobot_core.get_response(message)

    async def on_reaction_add(self, reaction, user):
        self.logger.info("Received reaction: {}".format(reaction.emoji))
        # if user != self.user:
        await self.brobot_core.handle_reaction(reaction, user)

    async def safe_send_message(self, dest, content):
        msg = None
        if len(content) == 0:
            return
        try:
            await self.send_typing(dest)
            time.sleep(1)
            if random.randint(0, 100) == 1:
                content = "Bananas!"
            if random.randint(0, 200) == 69:
                content = zalgo.main(content, "NEAR")
            if random.randint(0, 200) == 66:
                content = helper_functions.fork_it_up(content)
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

    async def guru_meditation(self, message, error):
        await self.safe_send_file(message.channel,
                                  "images/Guru_meditation.gif")
        await self.safe_send_message(message.channel, error)

    async def clean_shutdown(self, *args, **kwargs):
        self.brobot_core.dh.cleanup()
        await self.logout()
        return


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

# open secrets file for API token and start the bot
with open("data/SECRETS.yaml", 'r') as filein:
    secrets = yaml.load(filein)
data_handler = DataHandler()
bot = BroBotClient(data_handler)

for sig in (SIGTERM, SIGABRT, SIGINT):
    bot.loop.add_signal_handler(
        sig, lambda: asyncio.ensure_future(bot.clean_shutdown()))
    # signal(sig, bot.clean_shutdown)

bot.run(secrets["token"])


# make sure things get saved to file
@atexit.register
def save_stuff():
    bot.brobot_core.dh.cleanup()
