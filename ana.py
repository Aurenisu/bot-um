import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'BAŞARDIK! {bot.user} şu an çevrimiçi!')

@bot.command()
async def selam(ctx):
    await ctx.send('Selam! Sonunda beni calistirmayi basardin!')

bot.run('MTQ4NzgxNzA2MDUzMTgzMDk1NQ.Gic61K.SEGo6g9Wa6tPgCAJ-ppDl-MUpqWp06N-YL_jFI')