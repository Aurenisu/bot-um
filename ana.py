import discord
from discord import app_commands
from discord.ext import commands
import os
import yt_dlp
import asyncio

# --- 1. BOT AYARLARI VE YETKİLER ---
intents = discord.Intents.default()
intents.message_content = True  # Mesajları okuma yetkisi
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 2. MÜZİK MOTORU AYARLARI (GÜNCEL) ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': 'cookies.txt',  # GitHub'da cookies.txt dosyan olmalı!
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
    # Slash komutlarını senkronize et
    try:
        await bot.tree.sync()
        print(f"✅ BOT AKTİF: {bot.user}")
    except Exception as e:
        print(f"Senkronizasyon Hatası: {e}")

# --- 3. /cal KOMUTU ---
@bot.tree.command(name="cal", description="Şarkı çalmaya başlar")
@app_commands.describe(sarki="Şarkı adı veya YouTube linki")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer() # Bot 'düşünüyor' moduna girer
    
    # Kullanıcı ses kanalında mı?
    if not interaction.user.voice:
        return await interaction.followup.send("⚠️ Önce bir ses kanalına girmelisin!")

    # Kanala bağlan
    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    try:
        loop = asyncio.get_event_loop()
        # YouTube'da ara
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{sarki}", download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        url = data['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        # Zaten çalıyorsa durdur ve yenisini aç
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Şu an çalıyor: **{data['title']}**")
        
    except Exception as e:
        print(f"Oynatma Hatası: {e}")
        await interaction.followup.send(f"❌ Bir hata oluştu (Muhtemelen YouTube engeli): {e}")

# --- 4. /ayril KOMUTU ---
@bot.tree.command(name="ayril", description="Bot kanaldan ayrılır")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Görüşürüz! 👋")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.")

# --- 5. BOTU ÇALIŞTIR (GÜVENLİ YÖNTEM) ---
token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ HATA: DISCORD_TOKEN bulunamadı! Railway Variables kısmına ekle.")
