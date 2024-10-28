
from discord.ext import commands
import discord
from utils.utils import isAdmin
from discord import app_commands
import random
import requests
from typing import Optional

class MiscCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self._last_member = None

    @app_commands.command(name = "girlskissing", description="you see daughter, when two girls like eachother very much")
    async def girlkissing(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        #do not remove `rating:g`. the server will return porn lmao
        resp = requests.get("https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=2girls%20kiss%20rating:g")
        if resp.status_code == 200:
            pages = resp.json()["@attributes"]['count'] // 100
            resppage = requests.get(f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&pid={random.randint(1,pages)}&json=1&tags=2girls%20kiss%20rating:g")
            if resppage.status_code == 200:
                post = resppage.json()["post"][random.randint(0, len(resppage.json()["post"]))]
                embed = discord.Embed(title="post #7944344",
                      colour=0x00b0f4)

                embed.set_author(name="girls kissing")
                embed.add_field(name="uploaded by",value=post["owner"])
                embed.add_field(name="tags:", value=" ".join(post["tags"].split(" ")[:10]))
                embed.add_field(name="source", value=post["source"])

                embed.set_image(url=f"https://proxy.mono.exhq.dev/_/plain/{post["file_url"]}")

                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(content = "gelbooru shat itself lmaoooo")
        else:
            await interaction.followup.send(content = "gelbooru shat itself lmaoooo")



    @app_commands.command(name = "compliment", description="says something nice about you")
    async def compliment(self, interaction: discord.Interaction):
        comments = [ "You go, girl!", "Are you fucking kidding me? HELL yeah!", "Great job!", "I love it!", "Amazing work!", "Well done!", "Impressive!", "Fantastic!", "You nailed it!", "Awesome!", "Brilliant!", "Keep it up!" ] 
        random_comment = random.choice(comments) 
        await interaction.response.send_message(random_comment)

    @commands.command(name="sync", help="Syncs the tree (admin only)")
    async def sync_prefix(self, ctx: commands.Context, guild_id_to_sync: Optional[str] = None):
        self.client.tree.copy_global_to(guild=ctx.guild)
        commands = await self.client.tree.sync(guild=ctx.guild)


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
