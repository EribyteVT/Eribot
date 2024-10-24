from discord.ext import commands
import discord
from utils.utils import isAdmin,get_streamer_from_guild, get_user_token, add_twitch_event
from wrappers.CrudWrapper import CrudWrapper
import datetime
import pytz
from discord import app_commands
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, InvalidRefreshTokenException
from utils.Eribot_Views_Modals import GuildConnect
from wrappers.EncryptDecryptWrapper import EncryptDecryptWrapper

class TwitchCommands(commands.Cog):
    def __init__(self, client: commands.Bot ,crudService: CrudWrapper, guild_id_lookup, twitch: Twitch, encryptDecryptService: EncryptDecryptWrapper):
        self.client = client
        self._last_member = None
        self.crudService = crudService
        self.guild_id_lookup = guild_id_lookup
        self.twitch = twitch
        self.encryptDecryptService = encryptDecryptService

    
    
    
    @app_commands.command(name = "send-schedule-to-twitch", description="Sends stored schedule to twitch")
    async def sendToTwitch(self,interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        if not isAdmin(interaction.user):
            interaction.followup.send(content="Error, you are not an admin and not allowed to use this command", ephemeral=True)
            return


        streamer = await get_streamer_from_guild(interaction.guild.id,self.guild_id_lookup,self.crudService,True)


        if(not streamer.twitch_id):
            await interaction.followup.send(content="Error, please use /connect-guild-twitch to connect this guild to a streamer's twitch first")
            return

        token_data = self.crudService.get_token(streamer.twitch_id)

        if not token_data:
            await get_user_token(interaction,streamer.streamer_id, self.twitch)
            return
            


        refresh_token = self.encryptDecryptService.decrypt(token_data['data']["refreshToken"],token_data['data']["refreshSalt"])['decrypted']
        access_token = self.encryptDecryptService.decrypt(token_data['data']["accessToken"],token_data['data']["accessSalt"])['decrypted']

        target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]

        try:
            await self.twitch.set_user_authentication(access_token,target_scopes,refresh_token)
        except InvalidRefreshTokenException:
            await get_user_token(interaction,streamer.streamer_id)
            return


        

        streamList = self.crudService.getStreams(streamer.streamer_id)

        for stream in streamList:
            unixts = stream.unixts
            datetime_obj = datetime.datetime.fromtimestamp(unixts,tz=pytz.utc)
            stream.unixts = datetime_obj

        streamList.sort()

        bad_list = []
        for stream in streamList:
            try:
                if(not stream.twitch_id):
                    await add_twitch_event(stream, self.crudService, self.twitch, token_data)
            except:
                bad_list.append(stream.name)
        
        if(bad_list == []):
            await interaction.followup.send(content="Sent Schedule to twitch", ephemeral=True)
        else:
            message = ""
            for stream in bad_list:
                message += stream +'\n'
            await interaction.followup.send(content = "unable to add the following streams:\n"+message, ephemeral=True)
            

    @app_commands.command(name = "connect-guild-twitch", description="connects your guild to twitch")
    async def connectTwitch(self,interaction: discord.Interaction,username:str):
        if not isAdmin(interaction.user):
            interaction.response.send_message("Error, you are not an admin and not allowed to use this command")
            return
        
        streamer = await get_streamer_from_guild(interaction.guild.id, self.guild_id_lookup, self.client, self.crudService)
        
        user = self.twitch.get_users(logins=username)
        result = await first(user)

        if(result is None):
            await interaction.response.send_message("ERROR: twitch user not found", ephemeral=True)
            return

        embed = discord.Embed(title=result.login,description=f"date created: {result.created_at}")
        embed.set_image(url=result.profile_image_url)

        buttonMenu = GuildConnect(streamer.streamer_id,result.id,self.crudService)

        await interaction.response.send_message("# this you? ',:^)",embed=embed, ephemeral=True,view=buttonMenu)

        

  