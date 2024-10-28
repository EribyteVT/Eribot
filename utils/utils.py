from utils.Classes import Stream, Streamer
from wrappers.CrudWrapper import CrudWrapper
import datetime
import discord
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.oauth import UserAuthenticator
import pytz
import os

env = os.environ.get("ENV")

async def add_discord_event(interaction, stream: Stream, streamer: Streamer, crudService: CrudWrapper):
    event = await interaction.guild.create_scheduled_event(name = stream.name[:100], 
                                                                    description="Watch me live on twitch! :D", 
                                                                    start_time=stream.unixts, 
                                                                    end_time=stream.unixts + datetime.timedelta(minutes=stream.duration),
                                                                    location="https://twitch.tv/"+streamer.streamer_name,
                                                                    entity_type=discord.EntityType.external,
                                                                    privacy_level=discord.PrivacyLevel.guild_only)
    id = event.id
    crudService.addServiceIdToStream(stream.stream_id,"discord",None,id)

    return id

async def add_twitch_event(stream: Stream, crudService: CrudWrapper, twitch: Twitch, token_data):
    response = await twitch.create_channel_stream_schedule_segment(token_data['data']['twitchId'],stream.unixts,pytz.utc._tzname,is_recurring=False,
                                                                                duration=stream.duration,title=stream.name)
    id = response.segments[0].id
    crudService.addServiceIdToStream(stream.stream_id,"twitch",id,None)

    return id

async def addStreamerToGuildList(guild_id, sj, client, guild_id_lookup):
    streamer = Streamer(sj["streamerId"],sj["streamerName"],sj["timezone"],sj["guild"],sj["levelSystem"],sj["levelPingRole"],sj["levelChannel"], sj['twitchId'])
    
    if(streamer.level_system == "Y"):
        level_channel =  await client.fetch_channel(streamer.level_channel_id)
        streamer.setLevelChannel(level_channel)


    guild_id_lookup[guild_id] = streamer

    print("Cached Streamer")


async def get_streamer_from_guild(guild,guild_id_lookup,client ,crudService, force = False) -> Streamer:
    guild = str(guild)

    if (not guild in guild_id_lookup) or force :
        
        r = crudService.getStreamer(guild)
        await addStreamerToGuildList(guild,r['data'], client, guild_id_lookup)

    streamer = guild_id_lookup[guild]

    return streamer

def isAdmin(user):
    roles = user.roles 
    allowed = False
    for role in roles:
        if role.permissions.administrator:
            allowed = True 

    return allowed


async def get_user_token(interaction: discord.Interaction, twitch):
    target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]
    auth_url = UserAuthenticator(twitch, target_scopes, force_verify=False,url=f"https://auth-{env}.eribyte.net/").return_auth_url()
    await interaction.followup.send(content="Please authenticate your twitch account here first, once authenticated run this command again: " + auth_url,ephemeral=True)

async def add_xp_handler(id,xp_to_add, update, member, streamer, crudService):
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