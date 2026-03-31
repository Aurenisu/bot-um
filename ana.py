import discord
from discord import app_commands
from discord.ext import commands
import os
import yt_dlp
import asyncio

# --- 1. BOT AYARLARI ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 2. MÜZİK AYARLARI ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': 'cookies.txt',
    'no_warnings': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel quiet'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ BOT HAZIR: {bot.user} (Python 3.13)")

# --- 3. KOMUTLAR ---
@bot.tree.command(name="cal", description="Şarkı çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("⚠️ Önce bir ses kanalına gir!")

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{sarki}", download=False))
        if 'entries' in data: data = data['entries'][0]
        
        source = await discord.FFmpegOpusAudio.from_probe(data['url'], **FFMPEG_OPTIONS)
        
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Çalıyor: **{data['title']}**")
    except Exception as e:
        await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="ayril", description="Bot kanaldan çıkar")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Görüşürüz!")

# --- 4. ÇALIŞTIR ---
# Railway Variables kısmına DISCORD_TOKEN eklemeyi unutma!
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
