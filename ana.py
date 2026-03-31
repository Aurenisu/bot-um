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

# --- 2. MÜZİK MOTORU AYARLARI (HATASIZ) ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'cookiefile': 'cookies.txt',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'http_headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
    }
} # <-- Parantez burada kapandı!

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel quiet'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"✅ BOT ÇEVRİMİÇİ: {bot.user} (Python 3.11)")
    except Exception as e:
        print(f"Senkronizasyon hatası: {e}")

# --- 3. /cal KOMUTU ---
@bot.tree.command(name="cal", description="İstediğin şarkıyı çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        return await interaction.followup.send("⚠️ Önce bir ses kanalına gir!")

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    try:
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch1:{sarki}"
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
        
        if not data or 'entries' not in data or len(data['entries']) == 0:
            return await interaction.followup.send("❌ Şarkı bulunamadı veya YouTube engelledi.")

        entry = data['entries'][0]
        url = entry['url']
        title = entry.get('title', 'Bilinmeyen Şarkı')
        
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Şu an çalıyor: **{title}**")
        
    except Exception as e:
        print(f"Oynatma Hatası: {e}")
        await interaction.followup.send(f"❌ Hata: {str(e)[:100]}")

# --- 4. /ayril KOMUTU ---
@bot.tree.command(name="ayril", description="Botu kanaldan çıkarır")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Görüşürüz!")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.")

# --- 5. ÇALIŞTIRMA ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ HATA: DISCORD_TOKEN bulunamadı!")
