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
from math import floor
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from pyyoutube import Client

from CrudWrapper import parse_timestamp, CrudWrapper

class ConfirmationMenu(discord.ui.View):
    def __init__(self,discord_id,twitch_id):
        super().__init__()
        self.value = None
        self.discord_id = discord_id
        self.twitch_id = twitch_id

    # When the button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Connecting...',embed=None,view=None,delete_after=1)
        twitchUser = crudService.getDataFromTwitchdId(self.twitch_id)

        response = crudService.addTwitchToDiscord(self.discord_id,self.twitch_id)

        if(response.text == None or response.text == ""):
            await interaction.followup.send("ERROR ON BACKEND, SCHRODINGERS ACCOUNT EXISTS AND DOESNT",ephemeral=True)
            return
        
        await interaction.followup.send("Connected!!!!!",ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='No', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Very well, you can try again :3',embed=None,view=None)
        self.value = False
        self.stop()
        

comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
random_comment = random.choice(comments) 
print(random_comment)

intents = discord.Intents.all()
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)


env = "PROD"

crudService = CrudWrapper(env)

if(env == "PROD"):
    #THE MAIN ERIBYTE SERVER
    guild_id = '1144711250673148024'
    urlBase = 'http://10.0.0.6:8080'
    DTOKEN = Secrets.DISCORD_TOKEN

elif(env == "LOCAL"):
    #ERIBYTE TEST SITE ALPHA
    guild_id = '1166059727722131577'
    urlBase = 'http://127.0.0.1:8080'
    DTOKEN = Secrets.DISCORD_BETA_TOKEN
    
elif(env == "DEV"):
    #ERIBYTE TEST SITE ALPHA
    guild_id = '1166059727722131577'
    #can't be used locally
    urlBase = 'https://crud.eribyte.net'
    DTOKEN = Secrets.DISCORD_BETA_TOKEN

else:
    raise Exception("ERROR, ENV NOT SET")

#we use there later globally, which isn't the best practice but fuck it
LEVEL_CHANNEL = None
twitch = None 
youtube = None


class Stream:
    def __init__(self, unixts, name):
        self.unixts = unixts
        self.name = name
    def __lt__(self, other):
        return self.unixts < other.unixts
    def __str__(self):
        return self.name +', '+ str(self.unixts)


@tree.command(name = "compliment", description="says something nice about you",  guild=discord.Object(id=guild_id))
async def compliment(interaction: discord.Interaction):
    comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
    random_comment = random.choice(comments) 
    await interaction.response.send_message(random_comment)

@tree.command(name = "schedule",description="get the schedule for the next week", guild=discord.Object(id=guild_id))
async def schedule(interaction: discord.Interaction):
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
async def nextStream(interaction: discord.Interaction):
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
async def getLevel(interaction: discord.Interaction):
    #get id from user
    id = interaction.user.id

    #retrieve data from db
    data = crudService.getConnectedAccounts(id)

    accounts_xp = crudService.getXpFromAccounts(data)

    discrd_xp = crudService.getDataFromDiscordId(id)

    total_xp = discrd_xp['xp']

    #Shit way to do this, fix later, MVP Eribyte, MVP
    youtube_xp = "Not Connected"

    twitch_xp = "Not Connected (/connect-twitch to connect!)"

    for account in accounts_xp:
        total_xp += account['xp']
        if account['serviceName'] == "twitch":
            twitch_xp = account['xp']
        elif account['serviceName'] == "youtube":
            youtube_xp = account['xp']
    
    #get das levelin
    level = crudService.getLevelFromXp(total_xp)


    #format message
    message = f"# LEVEL: {level}\n# TOTAL XP: {total_xp}\n\n## discord: {discrd_xp['xp']}\n## twitch: {twitch_xp}\n"
    
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
    data = crudService.getDataFromTwitchdId(id)

    #if new account or time between messages is enuf, add xp
    if(data['lastMessageXp']==None or crudService.enoughTime(data['lastMessageXp'])):
        amount = random.randint(1,5)
        await add_xp_handler(id,amount,True)

@tree.command(name = "connect-twitch",description="connect your twitch and discord account for more XP!", guild=discord.Object(id=guild_id))
async def connectTwitch(interaction: discord.Interaction, username:str):

    id = interaction.user.id

    #check if twitch is connected
    if(crudService.twitchConnected(id)):
        await interaction.response.send_message("I'm sorry but you already have a twitch account connected [IF WANT DELETE TELL ERIBYTE]", ephemeral=True)
        return
    
    user = twitch.get_users(logins=username)
    result = await first(user)

    if(result is None):
        await interaction.response.send_message("ERROR: twitch user not found", ephemeral=True)
        return

    embed = discord.Embed(title=result.login,description=f"date created: {result.created_at}")
    embed.set_image(url=result.profile_image_url)

    buttonMenu = ConfirmationMenu(id, result.id)

    await interaction.response.send_message("# this you? ',:^)",embed=embed, ephemeral=True,view=buttonMenu)


# I HATE THE YOUTUBE API
# @tree.command(name = "connect-youtube",description="connect your youtube and discord account for more XP!", guild=discord.Object(id=guild_id))
# async def connectYoutube(interaction: discord.Interaction, username:str):

#     id = interaction.user.id

#     #check if twitch is connected
#     if(youtubeConnected(id)):
#         await interaction.response.send_message("I'm sorry but you already have a twitch account connected [IF WANT DELETE TELL ERIBYTE]", ephemeral=True)
#         return
    
#     # user = youtube.
    
#     user = twitch.get_users(logins=username)
#     result = await first(user)

#     if(result is None):
#         await interaction.response.send_message("ERROR: twitch user not found", ephemeral=True)
#         return

#     embed = discord.Embed(title=result.login,description=f"date created: {result.created_at}")
#     embed.set_image(url=result.profile_image_url)

#     buttonMenu = ConfirmationMenu(id, result.id)

#     await interaction.response.send_message("# this you? ',:^)",embed=embed, ephemeral=True,view=buttonMenu)


async def add_xp_handler(id,xp_to_add, update):
    data = crudService.getAssociatedFromDiscord(id)

    #not in db at all
    if(data == None or data == [] or data[0] == None):
        data = [crudService.getDataFromDiscordId(id)]

    total_xp = 0

    for account in data:
        total_xp += account['xp']    

    levelBefore = crudService.getLevelFromXp(total_xp)

    #if new account or time between messages is enuf, add xp
    data = crudService.addXpbyDiscordId(xp_to_add,id,update)
    total_xp += xp_to_add

    levelAfter = crudService.getLevelFromXp(total_xp)
        
    if(levelAfter > levelBefore):
       await LEVEL_CHANNEL.send(f"Congrats <@{id}> for reaching level {levelAfter}!!!")


@client.event
async def on_ready():
    global LEVEL_CHANNEL, twitch
    await client.change_presence(status=discord.Status.online)
    await tree.sync(guild=discord.Object(id=guild_id))

    if env == "PROD":
        LEVEL_CHANNEL = await client.fetch_channel('1188018666957189122')

    elif env == "DEV" or env == "LOCAL":
        LEVEL_CHANNEL = await client.fetch_channel('1188014511446302803')

    twitch = await Twitch(Secrets.APP_ID, Secrets.APP_SECRET)
    youtube = Client(api_key=Secrets.YOUTUBE_API_KEY)

    if on_ready :
        # called_once_a_day.start()
        print("RUNNING")

client.run(DTOKEN)