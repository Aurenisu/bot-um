import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random

# --- 1. AYARLAR ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.voice_states = True 
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
# BOM OYUNU İÇİN DEĞİŞKENLER
bom_sayi = 1
son_kisi = None

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
    print(f"✅ BOM VE EĞLENCE BOTU AKTİF: {bot.user}")

# --- 2. BOM OYUNU VE MESAJ PUAN SİSTEMİ ---
@bot.event
async def on_message(message):
    global bom_sayi, son_kisi
    if message.author.bot: return

    # BOM OYUNU KONTROLÜ (Sadece belirli bir kanalda olmasını istersen kanal ID ekleyebilirsin)
    # Örnek: if message.channel.id == 123456...
    content = message.content.strip()
    
    if content.isdigit():
        sayi = int(content)
        data = veri_yukle()
        uid = str(message.author.id)
        if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0}

        # Doğru sayı mı?
        if sayi == bom_sayi:
            if message.author.id == son_kisi:
                await message.add_reaction("❌")
                await message.channel.send(f"⚠️ {message.author.mention}, üst üste iki sayı yazamazsın! Oyun sıfırlandı.")
                bom_sayi = 1
                son_kisi = None
            else:
                await message.add_reaction("✅")
                bom_sayi += 1
                son_kisi = message.author.id
                data["kullanicilar"][uid]["puan"] += 2 # Her doğru sayıya 2 puan
                veri_kaydet(data)
        else:
            # Yanlış sayı yazılırsa
            await message.add_reaction("💀")
            await message.channel.send(f"❌ {message.author.mention} oyunu bozdu! Beklenen sayı: **{bom_sayi}**. Oyun 1'den tekrar başlıyor. (50 Puan Kaybettin)")
            data["kullanicilar"][uid]["puan"] -= 50
            bom_sayi = 1
            son_kisi = None
            veri_kaydet(data)

    # Normal mesaj puanı
    elif not message.content.startswith("/"):
        data = veri_yukle()
        uid = str(message.author.id)
        if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0}
        data["kullanicilar"][uid]["puan"] += 5
        veri_kaydet(data)

    await bot.process_commands(message)

# --- 3. YENİ OYUN KOMUTLARI ---

@bot.tree.command(name="bom_durum", description="Bom oyununda kaçıncı sayıda kalındığını gösterir")
async def bom_durum(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔢 Şu anki hedef sayı: **{bom_sayi}**")

@bot.tree.command(name="kayit", description="Kullanıcıyı etiketle ve kayıt et")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    data = veri_yukle()
    data["kullanicilar"][str(uye.id)] = {"isim": isim, "yas": yas, "puan": 100}
    veri_kaydet(data)
    try: await uye.edit(nick=f"{isim} | {yas}")
    except: pass
    await interaction.response.send_message(f"✅ {uye.mention} kayıt edildi.")

@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Puanın: **{p}**")

# --- MÜZİK KOMUTU (Basit Versiyon) ---
@bot.tree.command(name="cal", description="Müzik çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Sese gir!")
    if not interaction.guild.voice_client: await interaction.user.voice.channel.connect()
    
    YDL_OPTS = {'format': 'bestaudio/best', 'noplaylist': True, 'cookiefile': 'cookies.txt'}
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch1:{sarki}", download=False)['entries'][0]
        source = await discord.FFmpegOpusAudio.from_probe(info['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        if interaction.guild.voice_client.is_playing(): interaction.guild.voice_client.stop()
        interaction.guild.voice_client.play(source)
        await interaction.followup.send(f"🎵 Çalıyor: **{info['title']}**")

# --- DİĞER EĞLENCE KOMUTLARI ---
@bot.tree.command(name="ask_olcer", description="Aşk ölçer")
async def ask(interaction: discord.Interaction, uye: discord.Member):
    await interaction.response.send_message(f"❤️ {interaction.user.mention} ile {uye.mention} arasındaki aşk: **%{random.randint(0,100)}**")

bot.run(os.getenv('DISCORD_TOKEN'))
