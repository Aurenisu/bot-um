import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random
from datetime import datetime

# --- 1. AYARLAR ---
intents = discord.Intents.all() # Tüm izinleri açtık (Sıkıntı çıkmasın diye)
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
LOG_KANAL_ID = 123456789012345678 # <--- Burayı kendi kanal ID'nle değiştirmeyi unutma!
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

# --- KOMUTLARI ZORLA YÜKLEME ---
@bot.event
async def on_ready():
    print(f"🔄 Komutlar senkronize ediliyor...")
    try:
        # Bu satır komutları Discord'a anında işler!
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} adet komut başarıyla yüklendi!")
        print(f"🚀 Bot Hazır: {bot.user}")
    except Exception as e:
        print(f"❌ Senkronizasyon Hatası: {e}")

# --- 2. LOG SİSTEMİ ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    channel = bot.get_channel(LOG_KANAL_ID)
    if channel:
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Kullanıcı:", value=message.author.mention)
        embed.add_field(name="Mesaj:", value=message.content or "İçerik yok", inline=False)
        await channel.send(embed=embed)

# --- 3. BOM VE PUAN SİSTEMİ ---
@bot.event
async def on_message(message):
    global bom_sayi, son_kisi
    if message.author.bot: return

    content = message.content.strip().lower()
    data = veri_yukle()
    uid = str(message.author.id)
    if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0}

    # Gerçek BOM Kurallı Oyun
    if content == "bom" or content.isdigit():
        is_bom_turn = (bom_sayi % 5 == 0)
        success = (is_bom_turn and content == "bom") or (not is_bom_turn and content.isdigit() and int(content) == bom_sayi)

        if success:
            if message.author.id == son_kisi:
                await message.add_reaction("❌")
                bom_sayi = 1
                son_kisi = None
                await message.channel.send("⚠️ Sırayı bozdun (üst üste yazdın)! Oyun sıfırlandı.")
            else:
                await message.add_reaction("✅")
                bom_sayi += 1
                son_kisi = message.author.id
                data["kullanicilar"][uid]["puan"] += 5
                veri_kaydet(data)
        else:
            await message.add_reaction("💀")
            beklenen = "BOM" if is_bom_turn else str(bom_sayi)
            await message.channel.send(f"❌ Yanlış! Beklenen: **{beklenen}**. Oyun 1'den başlıyor.")
            data["kullanicilar"][uid]["puan"] = max(0, data["kullanicilar"][uid]["puan"] - 50)
            bom_sayi = 1
            son_kisi = None
            veri_kaydet(data)
    elif not message.content.startswith("/"):
        data["kullanicilar"][uid]["puan"] += 2
        veri_kaydet(data)

    await bot.process_commands(message)

# --- 4. TÜM KOMUTLAR ---
@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Puanın: **{p}**")

@bot.tree.command(name="kayit", description="Kullanıcıyı kayıt eder")
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    data = veri_yukle()
    data["kullanicilar"][str(uye.id)] = {"isim": isim, "yas": yas, "puan": 100}
    veri_kaydet(data)
    try: await uye.edit(nick=f"{isim} | {yas}")
    except: pass
    await interaction.response.send_message(f"✅ {uye.mention} kaydedildi!")

@bot.tree.command(name="cal", description="Müzik çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Sese gir!")
    vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
    
    YDL_OPTS = {'format': 'bestaudio/best', 'noplaylist': True, 'cookiefile': 'cookies.txt', 'default_search': 'ytsearch'}
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch1:{sarki}", download=False)['entries'][0]
        source = await discord.FFmpegOpusAudio.from_probe(info['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
        if vc.is_playing(): vc.stop()
        vc.play(source)
        await interaction.followup.send(f"🎵 Çalıyor: **{info['title']}**")

@bot.tree.command(name="temizle", description="Mesaj siler")
async def temizle(interaction: discord.Interaction, miktar: int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🧹 {miktar} mesaj temizlendi.", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
