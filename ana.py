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
intents.members = True # Kayıt sistemi için üye listesine erişim lazım
bot = commands.Bot(command_prefix="!", intents=intents)

# Verileri kaydetmek için basit bir sistem (Railway'de kalıcı olması için json kullanıyoruz)
DATA_FILE = "data.json"

def veri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"kullanicilar": {}}

def veri_kaydet(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- 2. MÜZİK MOTORU AYARLARI ---
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'cookiefile': 'cookies.txt'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ MEGA BOT AKTİF: {bot.user}")

# --- 3. KAYIT SİSTEMİ ---
@bot.tree.command(name="kayit", description="Sunucuya kayıt olmanı sağlar")
async def kayit(interaction: discord.Interaction, isim: str, yas: int):
    data = veri_yukle()
    uid = str(interaction.user.id)
    
    if uid in data["kullanicilar"]:
        return await interaction.response.send_message("Zaten kayıtlısın!", ephemeral=True)
    
    data["kullanicilar"][uid] = {"isim": isim, "yas": yas, "puan": 100, "rol": "Uye"}
    veri_kaydet(data)
    
    # İstersen burada otomatik rol de verdirebilirsin (Rol ID lazımdır)
    await interaction.response.send_message(f"✅ Kayıt başarılı! Hoş geldin **{isim}**. Başlangıç hediyesi 100 Puan verildi!")

# --- 4. PUAN VE OYUN SİSTEMİ ---
@bot.tree.command(name="puanim", description="Mevcut puanını gösterir")
async def puanim(interaction: discord.Interaction):
    data = veri_yukle()
    uid = str(interaction.user.id)
    puan = data["kullanicilar"].get(uid, {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Mevcut Puanın: **{puan}**")

@bot.tree.command(name="yazi_tura", description="Puanıyla yazı tura oyna")
async def yazi_tura(interaction: discord.Interaction, bahis: int, secim: str):
    data = veri_yukle()
    uid = str(interaction.user.id)
    
    if uid not in data["kullanicilar"] or data["kullanicilar"][uid]["puan"] < bahis:
        return await interaction.response.send_message("Yetersiz puan veya kayıtlı değilsin!")

    sonuc = random.choice(["yazi", "tura"])
    if secim.lower() == sonuc:
        data["kullanicilar"][uid]["puan"] += bahis
        mesaj = f"🎉 Kazandın! Sonuç: **{sonuc}**. Yeni puanın: {data['kullanicilar'][uid]['puan']}"
    else:
        data["kullanicilar"][uid]["puan"] -= bahis
        mesaj = f"💀 Kaybettin... Sonuç: **{sonuc}**. Kalan puanın: {data['kullanicilar'][uid]['puan']}"
    
    veri_kaydet(data)
    await interaction.response.send_message(mesaj)

# --- 5. YÖNETİM SİSTEMİ ---
@bot.tree.command(name="ban", description="Hatalı kullanıcıyı sunucudan yasaklar (Yönetici)")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Belirtilmedi"):
    await uye.ban(reason=sebep)
    await interaction.response.send_message(f"🚫 {uye.mention} sunucudan banlandı. Sebep: {sebep}")

@bot.tree.command(name="temizle", description="Mesajları toplu siler")
@app_commands.checks.has_permissions(manage_messages=True)
async def temizle(interaction: discord.Interaction, miktar: int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🧹 {miktar} adet mesaj temizlendi.", ephemeral=True)

# --- 6. MÜZİK SİSTEMİ (TEMEL) ---
@bot.tree.command(name="cal", description="Şarkı çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Sese gir!")
    if not interaction.guild.voice_client: await interaction.user.voice.channel.connect()
    
    data = ytdl.extract_info(f"ytsearch1:{sarki}", download=False)
    url = data['entries'][0]['url']
    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
    interaction.guild.voice_client.play(source)
    await interaction.followup.send(f"🎵 Çalıyor: **{data['entries'][0]['title']}**")

# --- ÇALIŞTIRMA ---
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
