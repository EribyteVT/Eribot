import discord 
import datetime
import pytz
import json
import CrudWrapper

class StreamInfo:
    def __init__(self, unixts,name,streamer_id):
        self.unixts = unixts
        self.name = name 
        self.streamer_id = streamer_id
    def __str__(self):
        return json.dumps({"unixts":self.unixts, "name":self.name,"streamer_id":self.streamer_id})


class ScheduleMenu(discord.ui.View):
    def __init__(self,streamList,streamer,crudService):
        super().__init__()
        self.streamList = streamList
        self.streamer = streamer
        self.crudService = crudService

        self.stream = None

        for stream in streamList:
            stream_info = StreamInfo(stream.unixts,stream.name,streamer.streamer_id)
            stream_time = datetime.datetime.fromtimestamp(stream.unixts).astimezone(pytz.timezone(streamer.timezone))

            stream_time_str = stream_time.strftime("%d/%m/%Y, %H:%M:%S")

            button = discord.ui.Button(label = stream_time_str + " " + stream.name,custom_id=str(stream_info))
            button.callback = self.handleClick
            self.add_button(button)
    def add_button(self,button):
        self.add_item(button)

    def clear(self):
        self.clear_items()

    async def handleClick(self,interaction:discord.Interaction):
        self.clear()
        self.next()

        self.stream = json.loads(interaction.data["custom_id"])

        await interaction.response.edit_message(content=f"{self.stream['name']} - <t:{str(self.stream['unixts']).split('.')[0]}>", view=self)
        
        print("click")

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

        modal = StreamNameModal(self.stream,self.crudService)
        await interaction.response.send_modal(modal)


    async def editTimeCallback(self,interaction:discord.Interaction):
        self.clear() 

        modal = StreamTimeModal(self.stream,self.crudService)
        await interaction.response.send_modal(modal)

    async def deleteCallback(self,interaction:discord.Interaction):
        self.crudService.deleteStream(self.stream["unixts"],self.stream["name"],self.stream["streamer_id"])
        await interaction.response.edit_message(content = "Deleted Stream!",view = None)

    

class StreamNameModal(discord.ui.Modal,title="New Stream Name"):
    def __init__(self,stream,crudService):
        super().__init__()

        self.custom_id = "MODAL"

        stream_name_input = discord.ui.TextInput(label = "New Stream Name",custom_id="NAME_ENTRY")
        self.add_item(stream_name_input)

        self.crudService = crudService
        self.stream = stream

        self.on_submit = self.name_callback
    
    async def name_callback(self,interaction:discord.Interaction):
        new_name = interaction.data["components"][0]["components"][0]["value"]

        self.crudService.editStream(self.stream["unixts"],self.stream["name"],self.stream["streamer_id"],self.stream["unixts"],new_name)

        await interaction.response.send_message("Changed!")
        

class StreamTimeModal(discord.ui.Modal,title="New Stream Time"):
    def __init__(self,stream,crudService):
        super().__init__()

        self.custom_id = "MODAL"

        stream_time_input = discord.ui.TextInput(label = "New Stream Time",custom_id="TIME_ENTRY")
        self.add_item(stream_time_input)

        self.crudService = crudService
        self.stream = stream

        self.on_submit = self.name_callback
    
    async def name_callback(self,interaction:discord.Interaction):
        new_time = interaction.data["components"][0]["components"][0]["value"]

        self.crudService.editStream(self.stream["unixts"],self.stream["name"],self.stream["streamer_id"],new_time,self.stream["name"])

        await interaction.response.send_message("Changed!")

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