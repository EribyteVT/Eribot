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
from twitchAPI.type import AuthScope, InvalidRefreshTokenException
from twitchAPI.oauth import UserAuthenticator

# from pyyoutube import Client
from CrudWrapper import parse_timestamp, CrudWrapper
from PIL import Image, ImageDraw, ImageFont
import os
import Eribot_Views_Modals
from typing import Optional, Union
import traceback
from schedule_maker import make_schedule
from EncryptDecryptWrapper import EncryptDecryptWrapper
from Classes import Stream, Streamer

    
# TODO: move to proper file
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

crudService = CrudWrapper(env,os.environ.get("CRUD_PASSWORD"), os.environ.get("CRUD_OAUTH_PASSWORD"))
encryptDecryptService = EncryptDecryptWrapper(env,os.environ.get("ENDPOINT_PASSWORD"))


# guild id to streamer obj
guild_id_lookup = {}

if(env == "PROD"):
    #THE MAIN ERIBYTE SERVER
    DTOKEN = os.environ.get("DISCORD_TOKEN")

elif(env == "LOCAL"):
    #ERIBYTE TEST SITE ALPHA
    DTOKEN = os.environ.get("DISCORD_BETA_TOKEN")

elif(env == "DEV"):
    DTOKEN = os.environ.get("DISCORD_BETA_TOKEN")

elif (env == "K8S_TEST_DEPLOY"):
    DTOKEN = os.environ.get("DISCORD_BETA_TOKEN")

else:
    raise Exception("ERROR, ENV NOT SET")

#we use there later globally, which isn't the best practice but fuck it
LEVEL_CHANNEL = None
twitch = None 
youtube = None





@tree.command(name = "compliment", description="says something nice about you")
async def compliment(interaction: discord.Interaction):
    comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
    random_comment = random.choice(comments) 
    await interaction.response.send_message(random_comment)

@tree.command(name = "schedule",description="get the schedule for the next week")
async def schedule(interaction: discord.Interaction):

    guild = str(interaction.guild_id)

    if not guild in guild_id_lookup:
        r = crudService.getStreamer(guild)
        if r == False:
            await interaction.response.send_message("Failed to get streamer from Database")
            return
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    streamList = crudService.getStreams(streamer.streamer_id)

    if len(streamList) == 0:
        await interaction.response.send_message("No Streams in the next week.")
        return

    streamList.sort()
    msg_to_send= ''

    for item in streamList:
        msg_to_send += f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
    
    if(msg_to_send == ''):
        msg_to_send = 'Error'
        
    await interaction.response.send_message(msg_to_send)
    pass

@tree.command(name = "next-stream",description="get the next stream")
async def nextStream(interaction: discord.Interaction):
    guild = str(interaction.guild_id)

    if not guild in guild_id_lookup:
        r = crudService.getStreamer(guild)
        if r == False:
            await interaction.response.send_message("Failed to get streamer from Database")
            return
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    streamList = crudService.getStreams(streamer.streamer_id)

    #sort by closest to furthest
    streamList.sort()
    msg_to_send= ''

    #incase it errors
    if(len(streamList) == 0):
        await interaction.response.send_message("No Streams in the next week.")
        return

    #format messages
    item = streamList[0]
    msg_to_send = f'{item.name} - <t:{str(item.unixts).split(".")[0]}> \n'
        
    #send message
    await interaction.response.send_message(msg_to_send)

@tree.command(name = "get-level",description="get your current level!")
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


@tree.command(name = "connect-twitch",description="connect your twitch and discord account for more XP!")
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

@tree.command(name = "add-stream", description="Add a stream to the database")
async def addStream(interaction: discord.Interaction, timestamp: str, stream_name: str):
    if isAdmin(interaction.user):
        guild = str(interaction.guild_id)

        if not guild in guild_id_lookup:
            
            r = crudService.getStreamer(guild)
            await addStreamerToGuildList(guild,r)

        streamer = guild_id_lookup[guild]

        response = crudService.addStream(timestamp,stream_name,streamer.streamer_id)

        if response == "False":
            await interaction.response.send_message("Error, invalid timestamp")
            return
        await interaction.response.send_message("That probabaly worked :D")
    else:
        await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***")

@tree.command(name = "add-events",description="add a weeks worth of events")
async def addEvents(interaction: discord.Interaction):
    if not isAdmin(interaction.user):
        await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***")
        return


    guild = str(interaction.guild_id)

    if not guild in guild_id_lookup:
        
        r = crudService.getStreamer(guild)
        if r == False:
            await interaction.response.send_message("Failed to get streamer from Database")
            return
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    streamList = crudService.getStreams(streamer.streamer_id)

    for stream in streamList:
        unixts = stream.unixts
        datetime_obj = datetime.datetime.fromtimestamp(unixts).astimezone(pytz.timezone(streamer.timezone))
        stream.unixts = datetime_obj

    streamList.sort()
    try:
        for stream in streamList:
            if(not stream.event_id):
                event = await interaction.guild.create_scheduled_event(name = stream.name[:100], 
                                                                description="Watch me live on twitch! :D", 
                                                                start_time=stream.unixts, 
                                                                end_time=stream.unixts + datetime.timedelta(hours=2),
                                                                location="https://twitch.tv/"+streamer.streamer_name,
                                                                entity_type=discord.EntityType.external,
                                                                privacy_level=discord.PrivacyLevel.guild_only)
                id = event.id

                crudService.addServiceIdToStream(stream.stream_id,"discord",None,id)
            
        await interaction.response.send_message("Events added!")

    except Exception as err:
        print(traceback.format_exc())
        await interaction.response.send_message("An error has occured")

@tree.command(name = "sync", description="Syncs the tree (admin only)")
async def sync(interaction: discord.Interaction, guild_id_to_sync: Optional[str]):
    await interaction.response.defer(thinking=True)
    if(isAdmin(interaction.user)):
        if(guild_id_to_sync == "ALL"):
            commands = await tree.sync()

        elif(guild_id_to_sync != None):
            commands = await tree.sync(guild=discord.Object(id=guild_id_to_sync))

        else:
            commands = await tree.sync(guild=interaction.guild)

        message = ""

        for command in commands:
            message += command.name +"\n"
        
        await interaction.followup.send(content = "Synced the following commands:\n"+message)
    else:
        await interaction.followup.send(content = "Insufficient permissions")


@tree.command(name = "schedule-image",description="Create an image with your schedule on it")
async def scheduleImage(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    guild = str(interaction.guild_id)

    if not guild in guild_id_lookup:
        
        r = crudService.getStreamer(guild)
        if r == False:
            await interaction.followup.send(content="Failed to get streamer from Database")
            return
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    streamList = crudService.getStreams(streamer.streamer_id)


    for stream in streamList:
        unixts = stream.unixts
        datetime_obj = datetime.datetime.fromtimestamp(unixts)
        stream.unixts = datetime_obj

    streamList.sort()

    make_schedule(streamer,streamList)

    base_path = "assets/"

    if os.path.exists(base_path + streamer.guild + '/'):
        base_path += streamer.guild + '/'
    else:
        base_path += 'default/'
        
    await interaction.followup.send(file = discord.File(base_path+"schedule.png"))


@tree.command(name = "edit-schedule",description="edit schedule")
async def editSchedule(interaction: discord.Interaction):
    if not isAdmin(interaction.user):
        await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***")
        return

    guild = str(interaction.guild_id)

    if not guild in guild_id_lookup:
        
        r = crudService.getStreamer(guild)
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    streamList = crudService.getStreams(streamer.streamer_id)

    streamList.sort()
        
    await interaction.response.send_message(view=Eribot_Views_Modals.ScheduleMenu(streamList,streamer,crudService,interaction,twitch,encryptDecryptService),ephemeral=True)


@tree.command(name = "send-schedule-to-twitch", description="Sends stored schedule to twitch")
async def sendToTwitch(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    if not isAdmin(interaction.user):
        interaction.followup.send(content="Error, you are not an admin and not allowed to use this command")
        return


    streamer = await get_streamer_from_guild(interaction.guild.id,True)


    if(not streamer.twitch_id):
        await interaction.followup.send(content="Error, please use /connect-guild-twitch to connect this guild to a streamer's twitch first")
        return

    token_data = crudService.get_token(streamer.twitch_id)

    if not token_data:
        await get_user_token(interaction,streamer.streamer_id)
        return
        


    refresh_token = encryptDecryptService.decrypt(token_data["refreshToken"],token_data["refreshSalt"])['decrypted']
    access_token = encryptDecryptService.decrypt(token_data["accessToken"],token_data["accessSalt"])['decrypted']

    target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]

    try:
        await twitch.set_user_authentication(access_token,target_scopes,refresh_token)
    except InvalidRefreshTokenException:
        await get_user_token(interaction,streamer.streamer_id)
        return


    

    streamList = crudService.getStreams(streamer.streamer_id)

    for stream in streamList:
        unixts = stream.unixts
        datetime_obj = datetime.datetime.fromtimestamp(unixts,tz=pytz.utc)
        stream.unixts = datetime_obj

    streamList.sort()

    bad_list = []
    for stream in streamList:
        try:
            if(not stream.twitch_id):
                response = await twitch.create_channel_stream_schedule_segment(token_data['twitchId'],stream.unixts,pytz.utc._tzname,is_recurring=False,duration=180,title=stream.name)
                id = response.segments[0].id
                crudService.addServiceIdToStream(stream.stream_id,"twitch",id,None)
        except:
            bad_list.append(stream.name)
    
    if(bad_list == []):
        await interaction.followup.send(content="Sent Schedule to twitch")
    else:
        message = ""
        for stream in bad_list:
            message += stream +'\n'
        await interaction.followup.send(content = "unable to add the following streams:\n"+message)
        


    


@tree.command(name = "connect-guild-twitch", description="connects your guild to twitch")
async def connectTwitch(interaction: discord.Interaction,username:str):
    if not isAdmin(interaction.user):
        interaction.response.send_message("Error, you are not an admin and not allowed to use this command")
        return
    
    streamer = await get_streamer_from_guild(interaction.guild.id)
    
    user = twitch.get_users(logins=username)
    result = await first(user)

    if(result is None):
        await interaction.response.send_message("ERROR: twitch user not found", ephemeral=True)
        return

    embed = discord.Embed(title=result.login,description=f"date created: {result.created_at}")
    embed.set_image(url=result.profile_image_url)

    buttonMenu = Eribot_Views_Modals.GuildConnect(streamer.streamer_id,result.id,crudService)

    await interaction.response.send_message("# this you? ',:^)",embed=embed, ephemeral=True,view=buttonMenu)

    

    


async def get_user_token(interaction: discord.Interaction, streamer_id: int):
    target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]
    auth_url = UserAuthenticator(twitch, target_scopes, force_verify=False,url="https://auth.eribyte.net/").return_auth_url()
    await interaction.followup.send(content="Please authenticate your twitch account here first, once authenticated run this command again: " + auth_url,ephemeral=True)


@client.event
async def on_message(message:discord.Message):
    #bots do not get levels cuz they are stinky
    if message.author == client.user:
        return 
    
    guild = str(message.guild.id)

    if not guild in guild_id_lookup:
        
        r = crudService.getStreamer(guild)
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    if streamer.level_system != "Y":
        return
    
    # get user id
    id = message.author.id 

    #get data from id
    data = crudService.getDataFromDiscordId(id)

    #if new account or time between messages is enuf, add xp
    if(data['lastMessageXp']==None or crudService.enoughTime(data['lastMessageXp'])):
        amount = random.randint(1,5)
        await add_xp_handler(id,amount,True,message.author, streamer)

@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    print("Reacted")


async def add_xp_handler(id,xp_to_add, update, member, streamer):
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

        level_role = streamer.level_ping_role

        can_ping = False
        for role in member.roles:
            if int(role.id) == int(level_role):
                can_ping = True

        if(can_ping):
            await streamer.level_channel.send(f"Congrats <@{id}> for reaching level {levelAfter}!!!")
        else:
            await streamer.level_channel.send(f"Congrats {member.display_name} for reaching level {levelAfter}!!!")

async def addStreamerToGuildList(guild_id, sj):
    streamer = Streamer(sj["streamerId"],sj["streamerName"],sj["timezone"],sj["guild"],sj["levelSystem"],sj["levelPingRole"],sj["levelChannel"], sj['twitchId'])
    
    if(streamer.level_system == "Y"):
        level_channel =  await client.fetch_channel(streamer.level_channel_id)
        streamer.setLevelChannel(level_channel)


    guild_id_lookup[guild_id] = streamer

    print("Cached Streamer")


async def get_streamer_from_guild(guild,force = False) -> Streamer:
    guild = str(guild)

    if (not guild in guild_id_lookup) or force :
        
        r = crudService.getStreamer(guild)
        await addStreamerToGuildList(guild,r)

    streamer = guild_id_lookup[guild]

    return streamer

def isAdmin(user):
    roles = user.roles 
    allowed = False
    for role in roles:
        if role.permissions.administrator:
            allowed = True 

    return allowed



@client.event
async def on_ready():
    global LEVEL_CHANNEL, twitch
    await client.change_presence(status=discord.Status.online)
    # await tree.sync(guild=discord.Object(id=1166059727722131577))

    twitch = await Twitch(os.environ.get("APP_ID"), os.environ.get("APP_SECRET"))

    # youtube = Client(api_key=Secrets.YOUTUBE_API_KEY)

    print("RUNNING")



client.run(DTOKEN)