import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os

# 1. BOT AYARLARI
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. MÜZİK MOTORU AYARLARI
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': 'cookies.txt',  # cookies.txt dosyan GitHub'da olmalı!
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
    # Slash komutlarını Discord'a tanıtır
    await bot.tree.sync()
    print(f"✅ BOT HAZIR: {bot.user} olarak giriş yapıldı!")

# 3. OYNATMA KOMUTU (/cal)
@bot.tree.command(name="cal", description="İstediğin şarkıyı çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    
    # Ses kanalı kontrolü
    if not interaction.user.voice:
        return await interaction.followup.send("⚠️ Önce bir ses kanalına girmen lazım!")
    
    # Kanala bağlanma
    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    try:
        loop = asyncio.get_event_loop()
        # YouTube'da arama yap
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{sarki}", download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        url = data['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        # Eğer zaten bir şey çalıyorsa durdur
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Şu an çalıyor: **{data['title']}**")
        
    except Exception as e:
        print(f"Hata: {e}")
        await interaction.followup.send(f"❌ Bir hata oluştu: {e}")

# 4. AYRILMA KOMUTU (/ayril)
@bot.tree.command(name="ayril", description="Bottan kurtulmanı sağlar")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Görüşürüz! 👋")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.")

# BURAYA DİKKAT: Tırnakların arasına kendi Token'ını yapıştır!
bot.run('BURAYA_DISCORD_TOKENINI_YAPISTIR')
