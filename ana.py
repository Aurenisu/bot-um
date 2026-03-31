import discord
from discord import app_commands
from discord.ext import commands
import os, yt_dlp, asyncio, json, random

# --- 1. AYARLAR ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.voice_states = True # Özel ses odası için şart!
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
OZEL_KATEGORI_ID = None # Buraya özel odaların açılacağı kategori ID'sini yazabilirsin

def veri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"kullanicilar": {}}

def veri_kaydet(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ V3 ULTIMATE AKTİF: {bot.user}")

# --- 2. ETİKETLİ KAYIT SİSTEMİ ---
@bot.tree.command(name="kayit", description="Bir kullanıcıyı etiketleyerek kayıt et")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def kayit(interaction: discord.Interaction, uye: discord.Member, isim: str, yas: int):
    data = veri_yukle()
    uid = str(uye.id)
    data["kullanicilar"][uid] = {"isim": isim, "yas": yas, "puan": 100}
    veri_kaydet(data)
    
    try:
        await uye.edit(nick=f"{isim} | {yas}")
    except:
        pass # Yetki yetmezse hata vermesin
        
    await interaction.response.send_message(f"✅ {uye.mention} başarıyla kayıt edildi! (Başlangıç: 100 Puan)")

# --- 3. EĞLENCE OYUNLARI (DC, BOM, AŞK, 8BALL) ---
@bot.tree.command(name="dc", description="Doğruluk mu Cesaretlik mi?")
async def dc(interaction: discord.Interaction):
    d = ["En son ne zaman yalan söyledin?", "Buradaki en gıcık olduğun kişi kim?", "Hiç kimseden gizli bir şey yaptın mı?"]
    c = ["Sıradaki şarkıyı avazın çıktığı kadar söyle!", "En son mesajlaştığın kişiye 'Seni seviyorum' yaz.", "Profil fotoğrafını 1 saatliğine komik bir şey yap."]
    secim = random.choice(["Doğruluk", "Cesaretlik"])
    gorev = random.choice(d if secim == "Doğruluk" else c)
    await interaction.response.send_message(f"🎲 **{secim}** seçildi!\n**Görev:** {gorev}")

@bot.tree.command(name="ask_olcer", description="Biriyle aşkını ölç")
async def ask_olcer(interaction: discord.Interaction, uye: discord.Member):
    oran = random.randint(0, 100)
    kalp = "❤️" if oran > 50 else "💔"
    await interaction.response.send_message(f"💘 {interaction.user.mention} x {uye.mention}\n**Aşk Oranı:** %{oran} {kalp}")

@bot.tree.command(name="8ball", description="Sihirli 8-Ball sorunu cevaplar")
async def eightball(interaction: discord.Interaction, soru: str):
    cevaplar = ["Kesinlikle", "Belki", "İmkansız", "Daha sonra sor", "Evet", "Hayır"]
    await interaction.response.send_message(f"🔮 **Soru:** {soru}\n**Cevap:** {random.choice(cevaplar)}")

# --- 4. ÖZEL SES ODASI SİSTEMİ ---
# Bir kanala girince otomatik oda açar
@bot.event
async def on_voice_state_update(member, before, after):
    AC_KANAL_ID = 123456789 # Buraya "Oda Oluştur" kanalının ID'sini yazmalısın!
    
    if after.channel and after.channel.id == AC_KANAL_ID:
        guild = member.guild
        kategori = after.channel.category
        yeni_kanal = await guild.create_voice_channel(name=f"🔊 {member.name}'in Odası", category=kategori)
        await member.move_to(yeni_kanal)
        
        def check(m, b, a):
            return len(yeni_kanal.members) == 0
            
        while True:
            await asyncio.sleep(5)
            if len(yeni_kanal.members) == 0:
                await yeni_kanal.delete()
                break

# --- 5. PUAN VE KELİME OYUNU TEMELİ ---
@bot.tree.command(name="kelime_oyunu", description="Rastgele bir kelime veririm, puan kazanırsın")
async def kelime_oyunu(interaction: discord.Interaction):
    kelimeler = ["elma", "bilgisayar", "discord", "python", "müzik"]
    hedef = random.choice(kelimeler)
    await interaction.response.send_message(f"🍎 Kelimeyi ilk yazan 50 puan kazanır: **{hedef}**")
    
    def check(m): return m.content.lower() == hedef and m.channel == interaction.channel
    
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        data = veri_yukle()
        uid = str(msg.author.id)
        if uid not in data["kullanicilar"]: data["kullanicilar"][uid] = {"isim": msg.author.name, "puan": 0}
        data["kullanicilar"][uid]["puan"] += 50
        veri_kaydet(data)
        await interaction.followup.send(f"🎉 Tebrikler {msg.author.mention}! 50 puan kazandın.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Kimse zamanında yazamadı.")

# --- MÜZİK VE DİĞERLERİ (Önceki koddan devam...) ---
# (Buraya önceki /cal, /ban komutlarını ekleyebilirsin, yer kaplamasın diye özet geçiyorum)

bot.run(os.getenv('DISCORD_TOKEN'))
