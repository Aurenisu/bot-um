import discord
from discord import app_commands
from discord.ext import commands
import os
import yt_dlp
import asyncio
import json
import random

# --- 1. BOT VE VERİ AYARLARI ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Geliştirici panelinden 'Server Members Intent'i açmayı unutma!
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"kullanicilar": {}}
    return {"kullanicilar": {}}

def veri_kaydet(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 2. MÜZİK MOTORU AYARLARI ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': 'cookies.txt',
    'default_search': 'ytsearch',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ MEGA BOT HAZIR: {bot.user}")

# --- 3. MESAJ BAŞINA PUAN SİSTEMİ ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = veri_yukle()
    uid = str(message.author.id)

    if uid not in data["kullanicilar"]:
        data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0, "seviye": 1}

    # Her mesajda 5 puan ekle
    data["kullanicilar"][uid]["puan"] += 5
    veri_kaydet(data)
    
    await bot.process_commands(message)

# --- 4. KAYIT VE PUAN KOMUTLARI ---
@bot.tree.command(name="kayit", description="Sunucuya resmi kayıt ol")
async def kayit(interaction: discord.Interaction, isim: str, yas: int):
    data = veri_yukle()
    uid = str(interaction.user.id)
    data["kullanicilar"][uid] = {"isim": isim, "yas": yas, "puan": 100, "kayitli": True}
    veri_kaydet(data)
    await interaction.response.send_message(f"✅ Hoş geldin {isim}! Hesabına 100 başlangıç puanı eklendi.")

@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Mevcut Puanın: **{p}**")

@bot.tree.command(name="siralam", description="Puan sıralamasını gösterir")
async def siralam(interaction: discord.Interaction):
    data = veri_yukle()
    sirali = sorted(data["kullanicilar"].items(), key=lambda x: x[1].get('puan', 0), reverse=True)
    msg = "🏆 **PUAN SIRALAMASI** 🏆\n"
    for i, (uid, info) in enumerate(sirali[:5], 1):
        msg += f"{i}. {info.get('isim', 'Bilinmeyen')} - {info.get('puan', 0)} Puan\n"
    await interaction.response.send_message(msg)

# --- 5. OYUN: YAZI TURA ---
@bot.tree.command(name="yazi_tura", description="Puanla yazı tura oyna")
async def yazi_tura(interaction: discord.Interaction, bahis: int, secim: str):
    data = veri_yukle()
    uid = str(interaction.user.id)
    user_data = data["kullanicilar"].get(uid)

    if not user_data or user_data["puan"] < bahis:
        return await interaction.response.send_message("❌ Yetersiz puan!")

    sonuc = random.choice(["yazi", "tura"])
    if secim.lower() == sonuc:
        data["kullanicilar"][uid]["puan"] += bahis
        await interaction.response.send_message(f"🎉 Bildin! Sonuç: **{sonuc}**. Kazandığın: {bahis}")
    else:
        data["kullanicilar"][uid]["puan"] -= bahis
        await interaction.response.send_message(f"💀 Kaybettin... Sonuç: **{sonuc}**. Giden: {bahis}")
    veri_kaydet(data)

# --- 6. MÜZİK KOMUTLARI ---
@bot.tree.command(name="cal", description="Müzik çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Sese gir!")
    
    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    try:
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch1:{sarki}", download=False))
        url = data['entries'][0]['url']
        title = data['entries'][0]['title']
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if interaction.guild.voice_client.is_playing(): interaction.guild.voice_client.stop()
        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Çalıyor: **{title}**")
    except Exception as e:
        await interaction.followup.send(f"Hata: {e}")

# --- 7. YÖNETİM KOMUTLARI ---
@bot.tree.command(name="temizle", description="Mesajları siler")
@app_commands.checks.has_permissions(manage_messages=True)
async def temizle(interaction: discord.Interaction, miktar: int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🧹 {miktar} mesaj temizlendi.", ephemeral=True)

@bot.tree.command(name="ban", description="Kullanıcıyı yasaklar")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Yok"):
    await uye.ban(reason=sebep)
    await interaction.response.send_message(f"🚫 {uye.name} banlandı. Sebep: {sebep}")

# --- BOTU ÇALIŞTIR ---
bot.run(os.getenv('DISCORD_TOKEN'))
