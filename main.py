import discord
from discord.ext import commands
from discord.utils import get
import logging
import os
import asyncio


handler = logging.FileHandler(filename='discord.log',encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print('-----')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    await bot.unload_extension(f'cogs.{extension}')
    await bot.load_extension(f'cogs.{extension}')
    await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    await bot.load_extension(f'cogs.{extension}')

@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    await bot.unload_extension(f'cogs.{extension}')

@bot.command()
async def help2(ctx):
    e = discord.Embed(
    title="Help",
    color=discord.Colour.blue(),
    description="This is the help command"
    )
    for cog_name, cog in bot.cogs.items():
        values = ' '.join(f'`{name}`' for name in cog.get_commands())
        e.add_field(name=cog_name, value=values, inline=True)
    await ctx.send(embed=e)

bot.run(TOKEN)
