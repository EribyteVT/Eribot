from discord.ext import commands
import discord
from utils.utils import isAdmin,get_streamer_from_guild
from wrappers.CrudWrapper import CrudWrapper
from discord import app_commands
from twitchAPI.twitch import Twitch
from wrappers.EncryptDecryptWrapper import EncryptDecryptWrapper
from utils.Eribot_Views_Modals import ScheduleMenu, DeleteMenu


class EditScheduleCommands(commands.Cog):
    def __init__(self, client: commands.Bot ,crudService: CrudWrapper, guild_id_lookup, twitch: Twitch, encryptDecryptService: EncryptDecryptWrapper):
        self.client = client
        self._last_member = None
        self.crudService = crudService
        self.guild_id_lookup = guild_id_lookup
        self.twitch = twitch
        self.encryptDecryptService = encryptDecryptService

            
    @app_commands.command(name = "add-stream", description="Add a stream to the database")
    async def addStream(self, interaction: discord.Interaction, timestamp: str, stream_name: str, duration: int = 150):
        if not isAdmin(interaction.user):
            await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***", ephemeral=True)
            return
        
        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        response = self.crudService.addStream(timestamp,stream_name,streamer.streamer_id, duration)

        if response == "False":
            await interaction.response.send_message("Error, invalid timestamp", ephemeral=True)
            return
        await interaction.response.send_message("That probabaly worked :D", ephemeral=True)
        

    @app_commands.command(name = "edit-schedule",description="edit schedule")
    async def editSchedule(self, interaction: discord.Interaction):
        if not isAdmin(interaction.user):
            await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***", ephemeral=True)
            return

        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        streamList = self.crudService.getStreams(streamer.streamer_id)

        streamList.sort()
            
        await interaction.response.send_message(view=ScheduleMenu(streamList,streamer,self.crudService,interaction,self.twitch,self.encryptDecryptService),ephemeral=True)

    @app_commands.command(name = "delete-stream",description="delete a stream schedule")
    async def deleteStream(self, interaction: discord.Interaction):
        if not isAdmin(interaction.user):
            await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***", ephemeral=True)
            return

        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        streamList = self.crudService.getStreams(streamer.streamer_id)

        streamList.sort()
            
        await interaction.response.send_message(view=DeleteMenu(streamList,streamer,self.crudService,interaction,self.twitch,self.encryptDecryptService),ephemeral=True)
