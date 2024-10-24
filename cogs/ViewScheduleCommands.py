from discord.ext import commands
import discord
from utils.utils import isAdmin,get_streamer_from_guild, add_discord_event
from wrappers.CrudWrapper import CrudWrapper
import datetime
import os
from discord import app_commands
from utils.schedule_maker import make_schedule


class ViewScheduleCommands(commands.Cog):
    def __init__(self, client: commands.Bot, crudService: CrudWrapper, guild_id_lookup):
        self.client = client
        self._last_member = None
        self.crudService = crudService
        self.guild_id_lookup = guild_id_lookup

    @app_commands.command(name = "schedule",description="get the schedule for the next week")
    async def schedule(self, interaction: discord.Interaction):

        # get the streamer from their guild
        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        # get the list of streamer's streams
        streamList = self.crudService.getStreams(streamer.streamer_id)

        # this means they have no streams
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

    @app_commands.command(name = "next-stream",description="get the next stream")
    async def nextStream(self, interaction: discord.Interaction):
        guild = str(interaction.guild_id)

        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        streamList = self.crudService.getStreams(streamer.streamer_id)

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

    @app_commands.command(name = "schedule-image",description="Create an image with your schedule on it")
    async def scheduleImage(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

        streamList = self.crudService.getStreams(streamer.streamer_id)

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

