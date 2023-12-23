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
from math import pow,floor

comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
random_comment = random.choice(comments) 
print(random_comment)
guild_id = '1144711250673148024'
LEVEL_CHANNEL = None
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


intents = discord.Intents.all()
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)
urlBase = 'http://10.0.0.6:8080'

DTOKEN = Secrets.DISCORD_TOKEN

@tree.command(name = "compliment", description="says something nice about you",  guild=discord.Object(id=guild_id))
async def compliment(interaction):
    comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
    random_comment = random.choice(comments) 
    await interaction.response.send_message(random_comment)
    


def parse_timestamp(timestamp):
    return datetime.datetime(*[int(x) for x in re.findall(r'\d+', timestamp)],tzinfo=pytz.utc)

@tree.command(name = "schedule",description="get the schedule for the next week", guild=discord.Object(id=guild_id))
async def schedule(interaction):
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    if(len(currentTime)<13):
        currentTime = currentTime.ljust(13,'0')

    url = urlBase + '/test/' + currentTime

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

@tree.command(name = "next-stream",description="get the next stream", guild=discord.Object(id=guild_id))
async def nextStream(interaction):
    #get current time in proper format
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    if(len(currentTime)<13):
        currentTime = currentTime.ljust(13,'0')

    #url for getting streams
    url = urlBase + '/test/' + currentTime

    #get streams
    r = requests.get(url)

    streamButFunky = r.json()

    streamList = []

    #clean steam data
    for stream in streamButFunky:
        unixts = parse_timestamp(stream["scheduleEntityKey"]['date'][:-5])
        unixts = datetime.datetime.timestamp(unixts)
        streamObj = Stream(unixts,stream['streamName'])
        streamList.append(streamObj)

    #sort by closest to furthest
    streamList.sort()
    msg_to_send= ''

    #incase it errors
    if(len(streamList)<0):
        interaction.response.send_message("Error retrieving entities from the databse")
        return

    #format messages
    item = streamList[0]
    msg_to_send = f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
        
    #send message
    await interaction.response.send_message(msg_to_send)

@tree.command(name = "get-level",description="get your current level!", guild=discord.Object(id=guild_id))
async def getLevel(interaction):
    #get id from user
    id = interaction.user.id

    #retrieve data from db
    data = getDataFromDiscordId(id)
    
    #get das levelin
    level = getLevelFromXp(data['xp'])

    #format message
    message = f"# LEVEL: {level}\n# XP: {data['xp']}"
    
    #send
    await interaction.response.send_message(message)

@client.event
async def on_message(message):
    #bots do not get levels cuz they are stinky
    if message.author == client.user:
        return 
    
    # get user id
    id = message.author.id 

    #get data from id
    data = getDataFromDiscordId(id)

    levelBefore = getLevelFromXp(data['xp'])
    
    #if new account or time between messages is enuf, add xp
    if(data['lastMessageXp']==None or enoughTime(data['lastMessageXp'])):
        data = addXp(random.randint(1,5),id,True)

    levelAfter = getLevelFromXp(data['xp'])
        
    if(levelAfter > levelBefore):
        await LEVEL_CHANNEL.send(f"Congrats <@{id}> for reaching level {levelAfter}!!!")


    
    
def getLevelFromXp(xp):
    """
    THE 2 FUNCTIONS FOR XP:
    0-50: 0.04x^3 + 0.8x^2 + 2x
    50+: 400(x-32.25)
    """
    #we have 2 different functions for xp, rollover xp is second function
    rollover_xp=0

    #split into 2 diff xp graphs
    if(xp>7100):
        rollover_xp = xp-7100
        xp=7100
    
    highestLevel = 0

    for i in range(51):
        xp_for_i = .04 * (i**3) + .8 * (i**2) + 2*i
        if xp >= xp_for_i:
            highestLevel = i

    level = highestLevel

    #always rollover, it's either 0 or something
    level += floor((rollover_xp)//400)

    return level

def getDataFromDiscordId(id):
    #ALSO ADDS USER BTW FUTURE ERIBYTE
    url = urlBase + '/getbyId/discord/'+str(id)

    #get data
    data = requests.get(url)

    #if none, add user
    if(data.text is None or data.text ==""):
        data = addXp(0,id,False)
    else:
        data = data.json()


    #return the data
    return data


def addXp(xp,id,update):
    #get current time in okay enough format
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    if(len(currentTime)==12):
        currentTime+='0'
    
    #data for update
    data = {"id":id,"xp":xp,"updateTime":update,"newTime":currentTime}

    #data to send update to
    url = urlBase + '/update/discord'

    #send request
    request = requests.post(url,json=data).json() 

    return request



def enoughTime(lastTime):
    #get current time
    currentTime = str(time.time())[:-4]
    currentTime = ''.join(currentTime.split('.'))

    if(len(currentTime)<13):
        currentTime = currentTime.ljust(13,'0')
    
    #how we tell if enough time has passed (a random 7-17 mins)
    bodgeTime = (12 + random.randint(-5,5))*60000 

    #real complicated logic to convert dates (man I fuckin hate dates)
    lastTime = datetime.datetime.timestamp(parse_timestamp(lastTime[:-5]))*1000

    #if it's been 7-17 minutes past the last update, update
    if(int(currentTime) > int(lastTime)+bodgeTime):
        return True 
    
    return False



@client.event
async def on_ready():
    global LEVEL_CHANNEL
    await client.change_presence(status=discord.Status.online)
    await tree.sync(guild=discord.Object(id=guild_id))
    LEVEL_CHANNEL = await client.fetch_channel('1188018666957189122')

    if on_ready :
        # called_once_a_day.start()
        print("RUNNING")

client.run(DTOKEN)