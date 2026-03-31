import discord
from discord.ext import commands
import os
import yt_dlp
import asyncio

# Botun yetkilerini açıyoruz
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Müzik ayarları
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print("Bot su an aktif ve muzik calabilir!")

@bot.command()
async def katil(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("Geldim! Ne çalıyoruz?")
    else:
        await ctx.send("Önce bir ses kanalına girmen lazım!")

@bot.command()
async def cal(ctx, *, search):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("Önce bir ses kanalına girmelisin!")
    
    async with ctx.typing():
        info = ytdl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
        url = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
    
    await ctx.send(f"Şu an çalıyor: **{info['title']}** 🎵")

@bot.command()
async def dur(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Müzik durduruldu. 🛑")

@bot.command()
async def ayril(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Görüşürüz! 👋")

bot.run(os.getenv('DISCORD_TOKEN'))
