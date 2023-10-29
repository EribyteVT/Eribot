import Secrets
import discord
from discord import app_commands
from discord.ext import tasks
import time
import requests
import datetime
import re
import random 
import pytz

comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
random_comment = random.choice(comments) 
print(random_comment)
# if(goingToCrash):
#     self.dont

class Stream:
    def __init__(self, unixts, name):
        self.unixts = unixts
        self.name = name
    def __lt__(self, other):
        return self.unixts < other.unixts
    def __str__(self):
        return self.name +', '+ str(self.unixts)


guild_id = "1144711250673148024"
intents = discord.Intents.all()
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

DTOKEN = Secrets.DISCORD_TOKEN

@tree.command(name = "compliment", description="says something nice about you",  guild=discord.Object(id='1144711250673148024'))
async def compliment(interaction):
    comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
    random_comment = random.choice(comments) 
    await interaction.response.send_message(random_comment)
    


def parse_timestamp(timestamp):
    return datetime.datetime(*[int(x) for x in re.findall(r'\d+', timestamp)],tzinfo=pytz.utc)

@tree.command(name = "schedule",description="get the schedule for the next week", guild=discord.Object(id='1144711250673148024'))
async def schedule(interaction):
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    url = 'http://10.0.0.6:8080/test/' + currentTime

    r = requests.get(url)

    print(r.status_code)

    streamButFunky = r.json()

    print(streamButFunky)

    streamList = []

    for stream in streamButFunky:
        unixts = parse_timestamp(stream["scheduleEntityKey"]['date'][:-5])
        unixts = datetime.datetime.timestamp(unixts)
        streamObj = Stream(unixts,stream['streamName'])
        streamList.append(streamObj)


    streamList.sort()
    msg_to_send= ''

    for item in streamList:
        msg_to_send += f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
    
    if(msg_to_send == ''):
        msg_to_send = 'Error getting from db, please try again'
        
    await interaction.response.send_message(msg_to_send)
    pass

@tree.command(name = "next-stream",description="get the next stream", guild=discord.Object(id='1144711250673148024'))
async def nextStream(interaction):
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    url = 'http://10.0.0.6:8080/test/' + currentTime

    r = requests.get(url)

    print(r.status_code)

    streamButFunky = r.json()

    print(streamButFunky)

    streamList = []

    for stream in streamButFunky:
        unixts = parse_timestamp(stream["scheduleEntityKey"]['date'][:-5])
        unixts = datetime.datetime.timestamp(unixts)
        streamObj = Stream(unixts,stream['streamName'])
        streamList.append(streamObj)


    streamList.sort()
    msg_to_send= ''

    if(len(streamList)<0):
        interaction.response.send_message("Error retrieving entities from the databse")
        return

    item = streamList[0]
    msg_to_send = f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
        
    await interaction.response.send_message(msg_to_send)

# @tasks.loop(seconds=60)
# async def called_once_a_day():
#     message_channel = None
#     async for guild in client.fetch_guilds(limit=150):
#         print('L + RATIO')
#         if guild.id == '1166059727722131577':
#             message_channel = guild.get_channel('1166059727722131580')

   
#     print(f"Got channel {message_channel}")
#     currentTime = str(time.time())[:-4]
#     currentTime = ''.join(currentTime.split('.'))

#     url = 'http://10.0.0.6:8080/test/' + currentTime

#     r = requests.get(url)

#     print(r.status_code)

#     streamButFunky = r.json()

#     print(streamButFunky)

#     streamList = []

#     for stream in streamButFunky:
#         unixts = parse_timestamp(stream["scheduleEntityKey"]['date'][:-5])
#         unixts = datetime.datetime.timestamp(unixts)
#         streamObj = Stream(unixts,stream['streamName'])
#         streamList.append(streamObj)


#     streamList.sort()
#     msg_to_send= ''

#     for item in streamList:
#         msg_to_send += f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
    
#     if(msg_to_send == ''):
#         msg_to_send = 'Error getting from db, please try again'

#     await message_channel.send(msg_to_send)

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    await tree.sync(guild=discord.Object(id=guild_id))

    if on_ready :
        # called_once_a_day.start()
        print("RUNNING")

client.run(DTOKEN)