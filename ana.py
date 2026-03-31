import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random
from datetime import datetime

# --- 1. AYARLAR ---
intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
LOG_KANAL_ID = 123456789012345678 # <--- KENDİ LOG KANALININ ID'SİNİ YAZ!
bom_sayi = 1
son_kisi = None

# YouTube Ayarları (Müzik için en stabil ayarlar)
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'addheader': [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')]
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {"kullanicilar": {}}
    return {"kullanicilar": {}}

def veri_kaydet(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ SİSTEM TAMAM: {bot.user}")

# --- 2. LOG SİSTEMİ ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    channel = bot.get_channel(LOG_KANAL_ID)
    if channel:
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Kullanıcı:", value=message.author.mention)
        embed.add_field(name="Mesaj:", value=message.content or "Boş", inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    channel = bot.get_channel(LOG_KANAL_ID)
    if channel:
        embed = discord.Embed(title="📝 Mesaj Düzenlendi", color=discord.Color.orange(), timestamp=datetime.now())
        embed.add_field(name="Kullanıcı:", value=before.author.mention)
        embed.add_field(name="Eski:", value=before.content, inline=False)
        embed.add_field(name="Yeni:", value=after.content, inline=False)
        await channel.send(embed=embed)

# --- 3. BOM VE PUAN (ON_MESSAGE) ---
@bot.event
async def on_message(message):
    global bom_sayi, son_kisi
    if message.author.bot: return
    content = message.content.strip().lower()
    data = veri_yukle()
    uid = str(message.author.id)
    if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0}

    if content == "bom" or content.isdigit():
        is_bom_turn = (bom_sayi % 5 == 0)
        success = (is_bom_turn and content == "bom") or (not is_bom_turn and content.isdigit() and int(content) == bom_sayi)
        if success:
            if message.author.id == son_kisi:
                bom_sayi, son_kisi = 1, None
                await message.channel.send("⚠️ Üst üste yazdın! Reset.")
            else:
                bom_sayi += 1
                son_kisi = message.author.id
                data["kullanicilar"][uid]["puan"] += 5
                veri_kaydet(data)
                await message.add_reaction("✅")
        else:
            await message.add_reaction("💀")
            bom_sayi, son_kisi = 1, None
            data["kullanicilar"][uid]["puan"] = max(0, data["kullanicilar"][uid]["puan"] - 50)
            veri_kaydet(data)
    await bot.process_commands(message)

# --- 4. KOMUTLAR ---

@bot.tree.command(name="cal", description="YouTube'dan müzik çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Önce sese gir!")
    
    vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
    
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{sarki}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
            
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            if vc.is_playing(): vc.stop()
            vc.play(source)
            await interaction.followup.send(f"🎵 Şu an çalıyor: **{title}**")
    except Exception as e:
        await interaction.followup.send(f"❌ Müzik hatası: {e}")

@bot.tree.command(name="yazi_tura", description="Yazı mı tura mı?")
async def yazi_tura(interaction: discord.Interaction):
    await interaction.response.send_message(f"🪙 **{random.choice(['Yazı', 'Tura'])}** geldi!")

@bot.tree.command(name="bom", description="BOM oyunu durumu")
async def bom_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔢 Sıradaki sayı: **{bom_sayi}**. 5'in katlarında BOM yaz!")

@bot.tree.command(name="kayit", description="Kullanıcıyı kaydet")
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    try:
        await uye.edit(nick=f"{isim} | {yas}")
        await interaction.response.send_message(f"✅ {uye.mention} kaydedildi.")
    except:
        await interaction.response.send_message("❌ Yetkim yetmedi, rolümü yukarı çek!")

@bot.tree.command(name="puan", description="Puan göster")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Puanın: {p}")

@bot.tree.command(name="temizle", description="Mesaj sil")
async def temizle(interaction: discord.Interaction, miktar: int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🧹 {miktar} mesaj silindi.", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
