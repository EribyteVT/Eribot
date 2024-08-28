import json
class Stream:
    def __init__(self, stream_id, unixts, streamer_id, name, event_id, twitch_id, duration, category_id  ):
        self.stream_id = stream_id
        self.unixts = unixts
        self.streamer_id = streamer_id
        self.name = name
        self.event_id = event_id
        self.twitch_id = twitch_id
        self.duration = duration
        self.category_id = category_id
    def __lt__(self, other):
        return self.unixts < other.unixts
    def __str__(self):
        return self.name +', '+ str(self.unixts)
    def json_dump(self):
        return json.dumps({"stream_id":self.stream_id,
                           "unixts":self.unixts, 
                           "streamer_id":self.streamer_id,
                           "name":self.name,
                           "event_id":self.event_id,
                           "twitch_id":self.twitch_id,
                           "duration":self.duration,
                           "category_id":self.category_id})
    
class Streamer:
    def __init__(self,streamer_id,streamer_name,timezone,guild,level_system,level_ping_role,level_channel,twitch_id, auto_discord_event, auto_twitch_schedule, auto_image_post, schedule_message_id, auto_change_schedule, image_message_id):
        self.streamer_id = str(streamer_id)
        self.streamer_name = str(streamer_name)
        self.timezone = str(timezone)
        self.guild = str(guild)
        self.level_system = str(level_system)
        self.level_ping_role = str(level_ping_role)
        self.level_channel_id = str(level_channel)
        self.level_channel = None
        self.twitch_id = twitch_id
        self.auto_discord_event = auto_discord_event
        self.auto_twitch_schedule = auto_twitch_schedule
        self.auto_image_post = auto_image_post
        self.schedule_message_id = schedule_message_id
        self.auto_change_schedule = auto_change_schedule
        self.image_message_id = image_message_id

    def setLevelChannel(self,level_channel):
        self.level_channel = level_channel