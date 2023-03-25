# bot.py
import os
import discord
import json

from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query, where
from datetime import datetime, timedelta, tzinfo

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.dm_reactions = True

load_dotenv()
LOVENSE_LINKS = json.loads(os.environ['LOVENSE_LINKS'])
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL = 707470444885704714
LOGCHANNEL = 831307521540358144
db = TinyDB('db.json')
reacts = TinyDB('reacts.json')
requests = TinyDB('requests.json')

Link = Query()

bot = commands.Bot(intents=discord.Intents.all(), command_prefix='!')
client = discord.Client(intents=intents)

ZERO = timedelta(0)


class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


@client.event
async def on_message(message):
    if message.channel == client.get_channel(CHANNEL):
        return 0
    if message.author == client.user:
        return 0
    if message.content.startswith(tuple(LOVENSE_LINKS)):
        channel = client.get_channel(CHANNEL)
        embedVar = discord.Embed(description=(
            "{} wants someone to control them. React below to request control."
            .format(message.author.mention)), color=0x00ff00)
        msg = await channel.send(embed=embedVar)
        User = Query()
        db.upsert({'name': message.author.id, 'link': message.content,
                  'msg': msg.id}, User.name == message.author.id)
        db.insert({'name': message.author.id,
                  'link': message.content, 'msg': msg.id})
        emoji = '👍'
        await msg.add_reaction(emoji)


@client.event
async def on_reaction_add(reaction, user):
    posted = reaction.message.created_at
    current = datetime.now(utc)
    diff = posted - current
    if (diff.total_seconds()/60 < 30):
        reaction.message.delete
    if not isinstance(reaction.message.channel, discord.DMChannel):
        if reaction.emoji == "👍":
            if user == client.user:
                return 0
            if (reaction.message.id in (reacts.search(where('name') == user.id))):
                return 0
            else:
                reacts.insert({'msg': reaction.message.id, 'usr': user.id})
                channel = client.get_channel(CHANNEL)
                result = db.get(Query()['msg'] == reaction.message.id)
                userID = int(result.get('name'))
                poster = await client.fetch_user(userID)
                msg = await poster.send("{} has requested control. Approve?".format(user.name))
                emoji = '👍'
                await msg.add_reaction(emoji)
                requests.insert({'msg': msg.id, 'name': user.id})

    else:
        if user == client.user:
            return 0
        result = requests.get(Query()['msg'] == reaction.message.id)
        userID = int(result.get('name'))
        requester = await client.fetch_user(userID)
        result = db.get(Query()['name'] == user.id)
        link = result.get('link')
        await requester.send("{} has approved you to control them".format(user.name))
        await requester.send("{}\n Use this link to control their toy.".format(link))
        await reaction.message.channel.send("You have approved {} to control your toy".format(requester.name))
        logchannel = client.get_channel(LOGCHANNEL)
        await logchannel.send("{} controlled {}".format(requester.mention, user.mention))
        await reaction.message.delete()
        result = db.get(Query()['name'] == user.id)
        messageID = int(result.get('msg'))
        channel = client.get_channel(CHANNEL)
        messageToDelete = await channel.fetch_message(messageID)
        embedVar = discord.Embed(description=(
            "{} Has been claimed".format(user.mention)), color=0x00ff00)
        await messageToDelete.edit(embed=embedVar)
        await messageToDelete.clear_reactions()

client.run(TOKEN)
