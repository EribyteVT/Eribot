import discord 
import datetime
import pytz
import json
import CrudWrapper
from Classes import Stream,Streamer
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
import EncryptDecryptWrapper


class StreamInfo:
    def __init__(self, unixts,name,streamer_id):
        self.unixts = unixts
        self.name = name 
        self.streamer_id = streamer_id
    def __str__(self):
        return json.dumps({"unixts":self.unixts, "name":self.name,"streamer_id":self.streamer_id})

class ScheduleMenu(discord.ui.View):
    def __init__(self,streamList: list[Stream],streamer:Streamer,crudService:CrudWrapper.CrudWrapper, interaction:discord.Interaction, twitch:Twitch,encryptDecryptService:EncryptDecryptWrapper):
        super().__init__()
        self.streamList = streamList
        self.streamer = streamer
        self.crudService = crudService
        self.interaction = interaction
        self.twitch = twitch
        self.encryptDecryptService = encryptDecryptService

        self.stream = None

        self.streamList = streamList

        for stream in streamList:
            stream_time = datetime.datetime.fromtimestamp(stream.unixts).astimezone(pytz.timezone(streamer.timezone))

            stream_time_str = stream_time.strftime("%d/%m/%Y, %H:%M:%S")

            button = discord.ui.Button(label = stream_time_str + " " + stream.name, custom_id=str(stream.stream_id))
            button.callback = self.handleClick
            self.add_button(button)
    
    def add_button(self,button):
        self.add_item(button)

    def clear(self):
        self.clear_items()

    async def handleClick(self,interaction:discord.Interaction):
        self.clear()

        for stream in self.streamList:
            print(stream)
            if(str(stream.stream_id) == interaction.data["custom_id"]):
                self.stream = stream 
                continue

        print(self.stream)

        
        modal = EditStreamModal(self.stream,self.crudService,self.streamer,self.interaction,self.twitch,self.encryptDecryptService)
        await interaction.response.send_modal(modal)

    async def deleteCallback(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True,ephemeral=True)
        message = ""

        if(self.stream.event_id):
            try:
                event = await interaction.guild.fetch_scheduled_event(self.stream.event_id)
                await event.cancel()
            except:
                message = "Error deleting discord event\n"
        if(self.stream.twitch_id):
            try:
                token_data = self.crudService.get_token(self.streamer.twitch_id)
                    


                refresh_token = self.encryptDecryptService.decrypt(token_data["refreshToken"],token_data["refreshSalt"])['decrypted']
                access_token = self.encryptDecryptService.decrypt(token_data["accessToken"],token_data["accessSalt"])['decrypted']

                target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]

                await self.twitch.set_user_authentication(access_token,target_scopes,refresh_token)

                print(self.stream.twitch_id)

                await self.twitch.delete_channel_stream_schedule_segment(self.streamer.twitch_id,self.stream.twitch_id)
            except:
                message += 'Error deleting twitch event\n'
        self.crudService.deleteStream(self.stream.stream_id)

        if(message == ""):
            message = "Deleted Stream!"
        
        await interaction.followup.send(content = message)

class EditStreamModal(discord.ui.Modal,title="Edit Stream data"):
    def __init__(self,stream:Stream,crudService:CrudWrapper.CrudWrapper,streamer:Streamer, interaction:discord.Interaction, twitch:Twitch,encryptDecryptService:EncryptDecryptWrapper):
        super().__init__()
        self.streamer = streamer
        self.twitch = twitch 
        self.encryptDecryptService = encryptDecryptService

        self.custom_id = "MODAL"

        stream_name_input = discord.ui.TextInput(label = "New Stream Name",custom_id="NAME_ENTRY", required=False)
        stream_time_input = discord.ui.TextInput(label = "New Stream Time",custom_id="TIME_ENTRY", required=False)
        stream_duration_input = discord.ui.TextInput(label = "New Stream Duration",custom_id="DURATION_ENTRY", required=False)

        self.add_item(stream_name_input)
        self.add_item(stream_time_input)
        self.add_item(stream_duration_input)

        self.crudService = crudService
        self.stream = stream

        self.on_submit = self.edit_callback


    async def edit_callback(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True,ephemeral=True)
        print(interaction.data)

        components = interaction.data['components']

        to_change = []

        new_name = components[0]["components"][0]['value']
        new_time = components[1]["components"][0]['value']
        new_duration = components[2]["components"][0]['value']

        if new_name != "":
            to_change.append("name")
        else:
            new_name = self.stream.name

        if new_time != "":
            new_time = int(new_time)
            to_change.append("time")
        else:
            new_time = self.stream.unixts

        if new_duration != "":
            new_duration = int(new_duration)
            to_change.append("duration")
        else:
            new_duration = self.stream.duration
            
        message = ""

        new_start_time = datetime.datetime.fromtimestamp(new_time).astimezone(pytz.timezone(self.streamer.timezone))

        if(self.stream.event_id):
            try:
                
                event = await interaction.guild.fetch_scheduled_event(self.stream.event_id)
                await event.edit(name=new_name,
                                start_time=new_start_time,
                                end_time=new_start_time + datetime.timedelta(minutes=new_duration))
            except:
                message = "Error with discord event\n"

        if(self.stream.twitch_id):
            try:
                token_data = self.crudService.get_token(self.streamer.twitch_id)

                refresh_token = self.encryptDecryptService.decrypt(token_data['data']["refreshToken"],token_data['data']["refreshSalt"])['decrypted']
                access_token = self.encryptDecryptService.decrypt(token_data['data']["accessToken"],token_data['data']["accessSalt"])['decrypted']

                target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]

                await self.twitch.set_user_authentication(access_token,target_scopes,refresh_token)

                print(self.stream.twitch_id)

                await self.twitch.update_channel_stream_schedule_segment(self.streamer.twitch_id,self.stream.twitch_id,title = new_name,start_time=new_start_time,duration=new_duration)
            except:
                message += 'Error with twitch event\n'


        if(message == ""):
            message = "Time updated!"

        self.crudService.editStream(self.stream.stream_id,to_change,new_name,new_time,new_duration)

        await interaction.followup.send(content = message, ephemeral=True)





class StreamTimeModal(discord.ui.Modal,title="New Stream Time"):
    def __init__(self,stream:Stream,crudService:CrudWrapper.CrudWrapper,streamer:Streamer, interaction:discord.Interaction, twitch:Twitch,encryptDecryptService:EncryptDecryptWrapper):
        super().__init__()
        self.streamer = streamer
        self.twitch = twitch 
        self.encryptDecryptService = encryptDecryptService

        self.custom_id = "MODAL"

        stream_time_input = discord.ui.TextInput(label = "New Stream Time",custom_id="TIME_ENTRY")
        self.add_item(stream_time_input)

        self.crudService = crudService
        self.stream = stream

        self.on_submit = self.name_callback
    
    async def name_callback(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        new_time = interaction.data["components"][0]["components"][0]["value"]

        new_time_datetime = datetime.datetime.fromtimestamp(float(new_time)).astimezone(pytz.timezone(self.streamer.timezone))

        print(new_time_datetime)
        new_endtime = new_time_datetime + datetime.timedelta(hours=2)

        message = ""

        if(self.stream.event_id):
            try:
                event = await interaction.guild.fetch_scheduled_event(self.stream.event_id)
                await event.edit(start_time=new_time_datetime,end_time=new_endtime)
            except:
                message = "Error with discord event\n"

        if(self.stream.twitch_id):
            try:
                token_data = self.crudService.get_token(self.streamer.twitch_id)
                    


                refresh_token = self.encryptDecryptService.decrypt(token_data["refreshToken"],token_data["refreshSalt"])['decrypted']
                access_token = self.encryptDecryptService.decrypt(token_data["accessToken"],token_data["accessSalt"])['decrypted']

                target_scopes = [AuthScope.CHANNEL_MANAGE_SCHEDULE]

                await self.twitch.set_user_authentication(access_token,target_scopes,refresh_token)

                print(self.stream.twitch_id)

                await self.twitch.update_channel_stream_schedule_segment(self.streamer.twitch_id,self.stream.twitch_id,start_time=new_time_datetime)
            except:
                message += 'Error deleting twitch event\n'

        
        if(message == ""):
            message = "Time updated!"

        self.crudService.editStream(self.stream.stream_id,"time",new_time,self.stream.name)

        await interaction.followup.send(content = message, ephemeral=True)

class GuildConnect(discord.ui.View):
    def __init__(self,streamer_id,twitch_id,crudService:CrudWrapper.CrudWrapper):
        super().__init__()
        self.value = None
        self.streamer_id  = streamer_id
        self.twitch_id = twitch_id
        self.crudService=crudService

    # When the button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Connecting...',embed=None,view=None,delete_after=1)

        response = self.crudService.addTwitchToStreamer(self.streamer_id,self.twitch_id)

        
        await interaction.followup.send(response,ephemeral=True)
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='No', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Very well, you can try again :3',embed=None,view=None)
        self.value = False
        self.stop()