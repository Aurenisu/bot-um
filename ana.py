import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_name="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {lolibot} olarak giriş yaptı!')

@bot.command()
async def selam(ctx):
    await ctx.send('Selam kardeşim, botun artık 7/24 aktif!')

bot.run(os.getenv('D
