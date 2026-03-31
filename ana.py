import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random
from datetime import datetime

# --- 1. AYARLAR ---
intents = discord.Intents.all() 
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
    # TÜM KOMUTLARI ZORLA SENKRONİZE ET
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} ADET KOMUT SENKRONİZE EDİLDİ!")
    except Exception as e:
        print(f"❌ Senkronizasyon Hatası: {e}")
    print(f"🚀 Bot Hazır: {bot.user}")

# --- 2. LOG SİSTEMİ ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    channel = bot.get_channel(LOG_KANAL_ID)
    if channel:
        embed = discord.Embed(title="🗑️ Mesaj Silindi", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="Kullanıcı:", value=message.author.mention)
        embed.add_field(name="Mesaj:", value=message.content or "İçerik boş", inline=False)
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

    # BOM OYUNU MANTIĞI
    if content == "bom" or content.isdigit():
        is_bom_turn = (bom_sayi % 5 == 0)
        success = (is_bom_turn and content == "bom") or (not is_bom_turn and content.isdigit() and int(content) == bom_sayi)

        if success:
            if message.author.id == son_kisi:
                await message.add_reaction("❌")
                bom_sayi, son_kisi = 1, None
                await message.channel.send("⚠️ Üst üste yazdın! Oyun sıfırlandı.")
            else:
                await message.add_reaction("✅")
                bom_sayi += 1
                son_kisi = message.author.id
                data["kullanicilar"][uid]["puan"] += 5
                veri_kaydet(data)
        else:
            await message.add_reaction("💀")
            beklenen = "BOM" if is_bom_turn else str(bom_sayi)
            await message.channel.send(f"❌ Yanlış! Beklenen: **{beklenen}**")
            data["kullanicilar"][uid]["puan"] = max(0, data["kullanicilar"][uid]["puan"] - 50)
            bom_sayi, son_kisi = 1, None
            veri_kaydet(data)
    elif not message.content.startswith("/"):
        data["kullanicilar"][uid]["puan"] += 2
        veri_kaydet(data)

    await bot.process_commands(message)

# --- 4. TÜM SLASH KOMUTLARI (EKSİKSİZ) ---

@bot.tree.command(name="puan", description="Puanını gösterir")
async def puan(interaction: discord.Interaction):
    data = veri_yukle()
    p = data["kullanicilar"].get(str(interaction.user.id), {}).get("puan", 0)
    await interaction.response.send_message(f"💰 Puanın: **{p}**")

@bot.tree.command(name="kayit", description="Kullanıcıyı kaydeder ve ismini değiştirir")
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    data = veri_yukle()
    data["kullanicilar"][str(uye.id)] = {"isim": isim, "yas": yas, "puan": 100}
    veri_kaydet(data)
    try: await uye.edit(nick=f"{isim} | {yas}")
    except: pass
    await interaction.response.send_message(f"✅ {uye.mention} kaydedildi!")

@bot.tree.command(name="siralam", description="Puan sıralaması")
async def siralam(interaction: discord.Interaction):
    data = veri_yukle()
    sirali = sorted(data["kullanicilar"].items(), key=lambda x: x[1].get('puan', 0), reverse=True)
    msg = "🏆 **PUAN SIRALAMASI** 🏆\n" + "\n".join([f"{i+1}. {u[1]['isim']} - {u[1]['puan']} Puan" for i, u in enumerate(sirali[:5])])
    await interaction.response.send_message(msg)

@bot.tree.command(name="ask_olcer", description="Aşk ölçer")
async def ask(interaction: discord.Interaction, uye: discord.Member):
    await interaction.response.send_message(f"❤️ {interaction.user.mention} x {uye.mention} Aşk: %{random.randint(0,100)}")

@bot.tree.command(name="dc", description="Doğruluk mu Cesaretlik mi?")
async def dc(interaction: discord.Interaction):
    soru = random.choice(["D: En sevdiğin renk?", "C: Komik bir ses çıkar!", "D: Hiç birinden gizlice hoşlandın mı?"])
    await interaction.response.send_message(f"🎲 {soru}")

@bot.tree.command(name="8ball", description="Sihirli 8-Ball")
async def eightball(interaction: discord.Interaction, soru: str):
    await interaction.response.send_message(f"🔮 **Soru:** {soru}\n**Cevap:** {random.choice(['Evet', 'Hayır', 'Belki', 'Kesinlikle!'])}")

@bot.tree.command(name="yazi_tura", description="Yazı mı tura mı?")
async def yazi_tura(interaction: discord.Interaction):
    await interaction.response.send_message(f"🪙 **{random.choice(['Yazı', 'Tura'])}** geldi!")

@bot.tree.command(name="cal", description="Müzik çalar")
async def cal(interaction: discord.Interaction, sarki: str):
    await interaction.response.defer()
    if not interaction.user.voice: return await interaction.followup.send("Sese gir!")
    vc = interaction.guild.voice_client or await interaction.user.voice.channel.connect()
    YDL_OPTS = {'format': 'bestaudio/best', 'noplaylist': True, 'cookiefile': 'cookies.txt', 'default_search': 'ytsearch'}
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{sarki}", download=False)['entries'][0]
            source = await discord.FFmpegOpusAudio.from_probe(info['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options='-vn')
            if vc.is_playing(): vc.stop()
            vc.play(source)
            await interaction.followup.send(f"🎵 Çalıyor: **{info['title']}**")
    except Exception as e: await interaction.followup.send(f"Hata: {e}")

@bot.tree.command(name="temizle", description="Mesaj siler")
@app_commands.checks.has_permissions(manage_messages=True)
async def temizle(interaction: discord.Interaction, miktar: int):
    await interaction.channel.purge(limit=miktar)
    await interaction.response.send_message(f"🧹 {miktar} silindi.", ephemeral=True)

bot.run(os.getenv('DISCORD_TOKEN'))
