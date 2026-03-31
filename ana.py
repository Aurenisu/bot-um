import discord
from discord import app_commands
from discord.ext import commands
import os
import yt_dlp
import asyncio

# Bot ayarları
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Müzik motoru ayarları
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    # Slash komutlarını Discord'a gönderiyoruz
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} adet slash komutu senkronize edildi!")
    except Exception as e:
        print(e)
    print(f"Bot {bot.user} olarak aktif, artik /cal kullanabilirsin!")

# /cal komutu
@bot.tree.command(name="cal", description="İstediğin şarkıyı çalar")
@app_commands.describe(sarki="Şarkı adı veya link")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer() # Botun düşünmesi için süre tanıyoruz
    
    if not interaction.user.voice:
        return await interaction.followup.send("Önce bir ses kanalına girmen lazım!")

    # Kanala bağlanma
    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    # Şarkıyı bulma
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(sarki, download=False))
    
    if 'entries' in data:
        data = data['entries'][0]
    
    url = data['url']
    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
    
    interaction.guild.voice_client.play(source)
    await interaction.followup.send(f"Şu an çalıyor: **{data['title']}** 🎵")

# /ayril komutu
@bot.tree.command(name="ayril", description="Bottan kurtulmanı sağlar")
async def ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Görüşürüz! 👋")
    else:
        await interaction.response.send_message("Zaten bir kanalda değilim.")

bot.run(os.getenv('DISCORD_TOKEN'))
