
from discord.ext import commands
import discord
from utils.utils import isAdmin
from discord import app_commands
import random
from typing import Optional

class MiscCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self._last_member = None

    @app_commands.command(name = "compliment", description="says something nice about you")
    async def compliment(self, interaction: discord.Interaction):
        comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
        random_comment = random.choice(comments) 
        await interaction.response.send_message(random_comment)

    @app_commands.command(name = "sync", description="Syncs the tree (admin only)")
    async def sync(self, interaction: discord.Interaction, guild_id_to_sync: Optional[str]):
        await interaction.response.defer(thinking=True)
        if(isAdmin(interaction.user)):
            if(guild_id_to_sync == "ALL"):
                commands = await self.client.tree.sync()

            elif(guild_id_to_sync != None):
                self.client.tree.copy_global_to(guild=discord.Object(id=guild_id_to_sync))
                commands = await self.client.tree.sync(guild=discord.Object(id=guild_id_to_sync))

            else:
                self.client.tree.copy_global_to(guild=interaction.guild)
                commands = await self.client.tree.sync(guild=interaction.guild)

            message = ""

            for command in commands:
                message += command.name +"\n"
            
            await interaction.followup.send(content = "Synced the following commands:\n"+message, ephemeral=True)
        else:
            await interaction.followup.send(content = "Insufficient permissions", ephemeral=True)
