import discord
from discord import app_commands
from discord.ext import commands
import os
import yt_dlp
import asyncio

# 1. Bot Ayarları ve Yetkiler
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Müzik Motoru Ayarları (Senin cookies.txt dosyanı kullanacak şekilde ayarlandı)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': './cookies.txt',  # Başına ./ ekleyerek "tam burada" dedik
    'no_warnings': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    # YouTube'u kandırmak için gerçek bir tarayıcı gibi davranıyoruz:
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel quiet'
}

# ytdl tanımlamasını buraya sabitledik
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} adet slash komutu senkronize edildi!")
    except Exception as e:
        print(f"Senkronizasyon hatası: {e}")
    print(f"Bot {bot.user} olarak aktif, artik /cal kullanabilirsin!")

# 3. /cal Komutu
@bot.tree.command(name="cal", description="İstediğin şarkıyı çalar")
@app_commands.describe(sarki="Şarkı adı veya link")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer() # Bot 'düşünüyor' moduna girer
    
    # Ses kanalı kontrolü
    if not interaction.user.voice:
        return await interaction.followup.send("Önce bir ses kanalına girmen lazım!")

    # Kanala bağlanma
    if not interaction.guild.voice_client:
        try:
            await interaction.user.voice.channel.connect()
        except Exception as e:
            return await interaction.followup.send(f"Kanala bağlanırken hata oluştu: {e}")

    # Şarkıyı arama ve oynatma
    try:
        loop = asyncio.get_event_loop()
        # Arama terimi (ytsearch) burada ekleniyor
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{sarki}", download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        url = data['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"Şu an çalıyor: **{data['title']}** 🎵")
        
    except Exception as e:
        print(f"Oynatma hatası: {e}")
        await interaction.followup.send(f"Bir hata oluştu: {e}")

# 4. /ayril Komutu
@bot.tree.command(name="ayril", description="Bottan kurtulmanı sağlar")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Görüşürüz! 👋")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.")

token = os.getenv('DISCORD_TOKEN')
if token is None:
    print("HATA: Token bulunamadı! Railway Variables kısmını kontrol et.")
else:
    bot.run(token)
