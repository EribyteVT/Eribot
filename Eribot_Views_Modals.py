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
        self.next()

        for stream in self.streamList:
            print(stream)
            if(str(stream.stream_id) == interaction.data["custom_id"]):
                self.stream = stream 
                continue

        print(self.stream)

        await interaction.response.edit_message(content=f"{self.stream.name} - <t:{str(self.stream.unixts).split('.')[0]}>", view=self)
        

    def next(self):


        name_button = discord.ui.Button(label = "Edit Name")
        name_button.callback=self.editNameCallback
        self.add_item(name_button)

        # edit time
        time_button = discord.ui.Button(label = "Edit Time")
        time_button.callback = self.editTimeCallback
        self.add_item(time_button)

        # delete
        delete_button = discord.ui.Button(label = "Delete", style=discord.ButtonStyle.danger)
        delete_button.callback = self.deleteCallback
        self.add_item(delete_button)

    async def editNameCallback(self,interaction:discord.Interaction):
        self.clear() 

        modal = StreamNameModal(self.stream,self.crudService,self.streamer,self.interaction,self.twitch,self.encryptDecryptService)
        await interaction.response.send_modal(modal)


    async def editTimeCallback(self,interaction:discord.Interaction):
        self.clear() 

        modal = StreamTimeModal(self.stream,self.crudService,self.streamer,self.interaction,self.twitch,self.encryptDecryptService)
        await interaction.response.send_modal(modal)

    async def deleteCallback(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
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
        await interaction.followup.send(content = message,ephemeral=True)


    

class StreamNameModal(discord.ui.Modal,title="New Stream Name"):
    def __init__(self,stream:Stream,crudService:CrudWrapper.CrudWrapper,streamer:Streamer, interaction:discord.Interaction, twitch:Twitch,encryptDecryptService:EncryptDecryptWrapper):
        super().__init__()
        self.streamer = streamer
        self.twitch = twitch 
        self.encryptDecryptService = encryptDecryptService

        self.custom_id = "MODAL"

        stream_name_input = discord.ui.TextInput(label = "New Stream Name",custom_id="NAME_ENTRY")
        self.add_item(stream_name_input)

        self.crudService = crudService
        self.stream = stream

        self.on_submit = self.name_callback
    
    async def name_callback(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True,ephemeral=True)
        new_name = interaction.data["components"][0]["components"][0]["value"]


        message = ""

        if(self.stream.event_id):
            try:
                event = await interaction.guild.fetch_scheduled_event(self.stream.event_id)
                await event.edit(name=new_name)
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

                await self.twitch.update_channel_stream_schedule_segment(self.streamer.twitch_id,self.stream.twitch_id,title=new_name)
            except:
                message += 'Error deleting twitch event\n'

        
        if(message == ""):
            message = "Name updated!"

        self.crudService.editStream(self.stream.stream_id,"name",self.stream.unixts,new_name)

        await interaction.followup.send(content=message,ephemeral=True)
        

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