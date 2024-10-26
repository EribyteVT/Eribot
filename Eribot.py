import discord
from discord.ext import commands
import random 
from twitchAPI.twitch import Twitch
import cogs.DiscordEventCommands
import cogs.EditScheduleCommands
import cogs.ExpCommands
import cogs.MiscCommands
import cogs.TwitchCommands
import cogs.ViewScheduleCommands
from wrappers.CrudWrapper import CrudWrapper
import os
from wrappers.EncryptDecryptWrapper import EncryptDecryptWrapper
import cogs

        
comments = ["You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
random_comment = random.choice(comments) 

intents = discord.Intents.all()
client = commands.Bot("Eri", intents = intents)

crudService = CrudWrapper(os.environ.get("CRUD_URL"),os.environ.get("CRUD_PASSWORD"), os.environ.get("CRUD_OAUTH_PASSWORD"))
encryptDecryptService = EncryptDecryptWrapper(os.environ.get("ENCRYPT_URL"),os.environ.get("ENDPOINT_PASSWORD"))

# guild id to streamer obj
guild_id_lookup = {}

DTOKEN = os.environ.get("DISCORD_TOKEN")

@client.event
async def on_ready():
    twitch = await Twitch(os.environ.get("APP_ID"), os.environ.get("APP_SECRET"))

    await client.add_cog(cogs.DiscordEventCommands.DiscordEventCommands(client,crudService,guild_id_lookup))
    await client.add_cog(cogs.EditScheduleCommands.EditScheduleCommands(client,crudService,guild_id_lookup,twitch, encryptDecryptService))
    await client.add_cog(cogs.ExpCommands.ExpCommands(client,crudService,twitch,guild_id_lookup))
    await client.add_cog(cogs.MiscCommands.MiscCommands(client))
    await client.add_cog(cogs.TwitchCommands.TwitchCommands(client,crudService,guild_id_lookup,twitch,encryptDecryptService))
    await client.add_cog(cogs.ViewScheduleCommands.ViewScheduleCommands(client,crudService,guild_id_lookup))

    await client.change_presence(status=discord.Status.online)
    
    print("RUNNING")



client.run(DTOKEN)
