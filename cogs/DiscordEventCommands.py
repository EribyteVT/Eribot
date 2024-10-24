from discord.ext import commands
import discord
from utils.utils import isAdmin,get_streamer_from_guild, add_discord_event
from wrappers.CrudWrapper import CrudWrapper
import datetime
import traceback
import pytz
from discord import app_commands


class DiscordEventCommands(commands.Cog):
    def __init__(self, bot, crudService: CrudWrapper, guild_id_lookup,):
        self.client = bot
        self._last_member = None
        self.crudService = crudService
        self.guild_id_lookup = guild_id_lookup

    
    @app_commands.command(name = "add-events",description="add a weeks worth of events")
    async def addEvents(self, interaction: discord.Interaction):
        try:
            if not isAdmin(interaction.user):
                await interaction.response.send_message("HEY LOSER MC DORK FACE, NICE TRY BUT UR NOT ***ALLOWED***", ephemeral=True)
                return


            streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)

            streamList = self.crudService.getStreams(streamer.streamer_id)

            for stream in streamList:
                unixts = stream.unixts
                datetime_obj = datetime.datetime.fromtimestamp(unixts).astimezone(pytz.timezone(streamer.timezone))
                stream.unixts = datetime_obj

            streamList.sort()

            try:
                for stream in streamList:
                    if(not stream.event_id):
                        await add_discord_event(interaction, stream, streamer,self.crudService)
                    
                await interaction.response.send_message("Events added!", ephemeral=True)
            except Exception as err:
                print(traceback.format_exc())
                await interaction.response.send_message("An error has occured", ephemeral=True)

        except Exception as err:
            print(traceback.format_exc())
            await interaction.response.send_message("An error has occured", ephemeral=True)