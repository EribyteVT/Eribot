from discord.ext import commands
import discord
from utils.utils import addStreamerToGuildList, add_xp_handler
from wrappers.CrudWrapper import CrudWrapper
import random
from discord import app_commands
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from utils.Eribot_Views_Modals import ConfirmationMenu

class ExpCommands(commands.Cog):
    def __init__(self, client: commands.Bot ,crudService: CrudWrapper, twitch: Twitch, guild_id_lookup):
        self.client = client
        self._last_member = None
        self.crudService = crudService
        self.twitch = twitch
        self.guild_id_lookup = guild_id_lookup
        

    @app_commands.command(name = "connect-twitch",description="connect your twitch and discord account for more XP!")
    async def connectTwitch(self, interaction: discord.Interaction, username:str):

        id = interaction.user.id

        #check if twitch is connected
        if(self.crudService.twitchConnected(id)):
            await interaction.response.send_message("I'm sorry but you already have a twitch account connected [IF WANT DELETE TELL ERIBYTE]", ephemeral=True)
            return
        
        user = self.twitch.get_users(logins=username)
        result = await first(user)

        if(result is None):
            await interaction.response.send_message("ERROR: twitch user not found", ephemeral=True)
            return

        embed = discord.Embed(title=result.login,description=f"date created: {result.created_at}")
        embed.set_image(url=result.profile_image_url)

        buttonMenu = ConfirmationMenu(id, result.id, self.crudService)

        await interaction.response.send_message("# this you? ',:^)",embed=embed, ephemeral=True,view=buttonMenu)

    @app_commands.command(name = "get-level",description="get your current level!")
    async def getLevel(self,interaction: discord.Interaction):
        #get id from user
        id = interaction.user.id

        #retrieve data from db
        data = self.crudService.getConnectedAccounts(id)

        accounts_xp = self.crudService.getXpFromAccounts(data)

        discrd_xp = self.crudService.getDataFromDiscordId(id)

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
        level = self.crudService.getLevelFromXp(total_xp)


        #format message
        message = f"# LEVEL: {level}\n# TOTAL XP: {total_xp}\n\n## discord: {discrd_xp['xp']}\n## twitch: {twitch_xp}\n"
        
        #send
        await interaction.response.send_message(message)

    @commands.Cog.listener("on_message")
    async def on_message(self, message:discord.Message):
        #bots do not get levels cuz they are stinky
        if message.author == self.client.user:
            return 
        
        guild = str(message.guild.id)

        if not guild in self.guild_id_lookup:
            
            r = self.crudService.getStreamer(guild)
            await addStreamerToGuildList(guild,r,self.client,self.guild_id_lookup)

        streamer = self.guild_id_lookup[guild]

        if streamer.level_system != "Y":
            return
        
        # get user id
        id = message.author.id 

        #get data from id
        data = self.crudService.getDataFromDiscordId(id)

        #if new account or time between messages is enuf, add xp
        if(data['lastMessageXp']==None or self.crudService.enoughTime(data['lastMessageXp'])):
            amount = random.randint(1,5)
            await add_xp_handler(id,amount,True,message.author, streamer)

    