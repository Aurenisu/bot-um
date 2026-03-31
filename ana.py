import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random
from datetime import datetime

# --- 1. AYARLAR ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.voice_states = True 
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
LOG_KANAL_ID = 123456789012345678 # <--- BURAYA KENDİ LOG KANALININ ID'SİNİ YAZ!
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
    print(f"✅ TÜM KOMUTLAR YÜKLENDİ: {bot.user}")

# --- 2. LOG SİSTEMİ ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    channel = bot.get_channel(LOG_KANAL_ID)
    if channel:
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Kullanıcı:", value=message.author.mention)
        embed.add_field(name="Kanal:", value=message.channel.mention)
        embed.add_field(name="Mesaj:", value=message.content or "İçerik yok", inline=False)
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

# --- 3. BOM VE PUAN SİSTEMİ ---
@bot.event
async def on_message(message):
    global bom_sayi, son_kisi
    if message.author.bot: return

    content = message.content.strip().lower()
    data = veri_yukle()
    uid = str(message.author.id)
    if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": message.author.name, "puan": 0}

    # Bom ve Sayı Kontrolü
    if content == "bom" or content.isdigit():
        is_bom_turn = (bom_sayi % 5 == 0)
        success = (is_bom_turn and content == "bom") or (not is_bom_turn and content.isdigit() and int(content) == bom_sayi)

        if success:
            if message.author.id == son_kisi:
                await message.add_reaction("❌")
                bom_sayi = 1
                son_kisi = None
                await message.channel.send("⚠️ Üst üste yazdın, oyun sıfırlandı!")
            else:
                await message.add_reaction("✅")
                bom_sayi += 1
                son_kisi = message.author.id
                data["kullanicilar"][uid]["puan"] += 5
                veri_kaydet(data)
        else:
            await message.add_reaction("💀")
            beklenen = "BOM" if is_bom_turn else str(bom_sayi)
            await message.channel.send(f"❌ Yandın! Beklenen: {beklenen}")
            data["kullanicilar"][uid]["puan"] = max(0, data["kullanicilar"][uid]["puan"] - 50)
            bom_sayi = 1
            son_kisi = None
            veri_kaydet(data)
    elif not message.content.startswith("/"):
        data["kullanicilar"][uid]["puan"] += 2
        veri_kaydet(data)

    await bot.process_commands(message)

# --- 4. TÜM SLASH KOMUTLARI ---

@bot.tree.command(name="kayit", description="Kullanıcıyı etiketle ve kayıt et")
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    data = veri_yukle()
    data["kullanicilar"][str(uye.id)] = {"isim": isim, "yas": yas, "puan": 100}
    veri_kaydet(data)
    try: await uye.edit(nick=f"{isim} | {yas}")
    except: pass
    await interaction.response.send_message(f"✅ {uye.mention} kayıt edildi!")

@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Puanın: **{p}**")
