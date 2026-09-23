"""
🐺 WHITE_WOLF KITT Voice TTS Bot - FINAL
Kew voice e join korle bot nije VC te join hoye mukhe bolbe!
"Joy join korse" "Joy leave nise" - Voice e bolbe, text e na!

Render 100% Working - with FFmpeg + gTTS
"""

import os
import asyncio
import threading
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from gtts import gTTS

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))
VOICE_LANG = os.getenv('VOICE_LANG', 'en')  # en or bn

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | LANG={VOICE_LANG}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# ========== WEB SERVER FOR RENDER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Voice TTS Bot Running')
        else:
            self.wfile.write(b'WHITE_WOLF Voice TTS Bot Alive - Joins VC and Speaks!')
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Web server on 0.0.0.0:{PORT}...", flush=True)
        httpd = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ WEB SERVER LISTENING on 0.0.0.0:{PORT}", flush=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"❌ Web error: {e}", flush=True)

threading.Thread(target=start_web, daemon=True).start()
time.sleep(1)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Guild wise voice client lock to avoid overlapping speech
speaking_locks = {}

async def speak_in_vc(guild, text, channel_to_join=None):
    """
    Bot VC te join hoye text ta bolbe
    """
    try:
        # Get or create lock for this guild
        if guild.id not in speaking_locks:
            speaking_locks[guild.id] = asyncio.Lock()
        
        async with speaking_locks[guild.id]:
            voice_client = guild.voice_client
            
            # If bot not in VC, join the target channel
            if voice_client is None and channel_to_join:
                print(f"🔊 Joining VC: {channel_to_join.name} in {guild.name}", flush=True)
                try:
                    voice_client = await channel_to_join.connect()
                except discord.ClientException:
                    # Already connected somewhere, move
                    voice_client = guild.voice_client
                    if voice_client:
                        await voice_client.move_to(channel_to_join)
                except Exception as e:
                    print(f"❌ Failed to join VC {channel_to_join.name}: {e}", flush=True)
                    return
            
            # If channel_to_join given and bot in different channel, move
            if voice_client and channel_to_join and voice_client.channel.id != channel_to_join.id:
                print(f"🔄 Moving to {channel_to_join.name}", flush=True)
                await voice_client.move_to(channel_to_join)
            
            if not voice_client:
                print(f"❌ No voice client for {guild.name}", flush=True)
                return

            # Generate TTS
            # Use bn for Bangla, en for English - gTTS supports both
            # If text has Bangla, use bn else en
            lang = VOICE_LANG
            # Auto detect if Bangla characters
            if any('\u0980' <= c <= '\u09FF' for c in text):
                lang = 'bn'
            
            filename = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
            print(f"🗣️ TTS Generating: '{text}' lang={lang} -> {filename}", flush=True)
            
            try:
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(filename)
            except Exception as e:
                print(f"❌ gTTS failed (lang {lang}), trying en: {e}", flush=True)
                # Fallback to English
                try:
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(filename)
                except Exception as e2:
                    print(f"❌ gTTS fallback failed: {e2}", flush=True)
                    return

            # Play audio
            try:
                # Check ffmpeg exists
                audio_source = discord.FFmpegPCMAudio(filename, options='-vn')
                
                if voice_client.is_playing():
                    voice_client.stop()
                
                print(f"▶️ Playing: {text}", flush=True)
                voice_client.play(audio_source)
                
                # Wait until finished
                while voice_client.is_playing():
                    await asyncio.sleep(0.5)
                
                print(f"✅ Finished speaking: {text}", flush=True)
                
            except discord.errors.ClientException as e:
                print(f"❌ FFmpeg error - is ffmpeg installed? {e}", flush=True)
                print("   -> Render buildCommand e 'apt-get install -y ffmpeg' add koro", flush=True)
            except Exception as e:
                print(f"❌ Play error: {e}", flush=True)
            finally:
                # Cleanup file
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except:
                    pass

    except Exception as e:
        print(f"❌ speak_in_vc error: {e}", flush=True)
        import traceback
        traceback.print_exc()

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 WHITE_WOLF VOICE TTS BOT ONLINE!\n🤖 {bot.user} | Guilds: {len(bot.guilds)}\n🎙️ Mode: Bot will JOIN VC and SPEAK!\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Voice Joins | !help"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | Guild: {member.guild.name}", flush=True)

    try:
        # === JOIN ===
        if before.channel is None and after.channel is not None:
            # Someone joined VC
            text_bangla = f"{member.display_name} voice e join korse"
            text_english = f"{member.display_name} joined {after.channel.name}"
            # Use Bangla as user requested
            text = text_bangla
            
            print(f"   -> JOIN: {text} | Channel: {after.channel.name}", flush=True)
            await speak_in_vc(member.guild, text, after.channel)

        # === LEAVE ===
        elif before.channel is not None and after.channel is None:
            # Someone left VC
            # If bot is in same channel and now channel empty (only bot left), bot will speak then leave
            voice_client = member.guild.voice_client
            
            text_bangla = f"{member.display_name} voice theke leave nise"
            text_english = f"{member.display_name} left {before.channel.name}"
            text = text_bangla
            
            print(f"   -> LEAVE: {text} | Channel: {before.channel.name}", flush=True)
            
            if voice_client and voice_client.channel.id == before.channel.id:
                # Bot is in same channel where person left
                # Speak first
                await speak_in_vc(member.guild, text, before.channel)
                
                # Check if channel now empty (only bot)
                await asyncio.sleep(1)
                if len(before.channel.members) == 1 and before.channel.members[0].bot:
                    print(f"   -> Channel {before.channel.name} empty, leaving...", flush=True)
                    await asyncio.sleep(2)
                    await voice_client.disconnect()
            else:
                # Bot not in that channel, try to join and speak? Or just ignore
                # For leave, we can join to speak if bot was not there? Let's not join for leave if bot not there
                # But if user wants bot to always speak, we can join before channel? No, channel already empty for that user
                # So only speak if bot already in that channel
                if voice_client:
                    await speak_in_vc(member.guild, text, voice_client.channel)

        # === MOVE ===
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text_bangla = f"{member.display_name} {before.channel.name} theke {after.channel.name} e move korse"
            text = text_bangla
            print(f"   -> MOVE: {text}", flush=True)
            await speak_in_vc(member.guild, text, after.channel)

    except Exception as e:
        print(f"❌ Voice event error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# ========== COMMANDS ==========
@bot.command(name="join")
async def join_cmd(ctx):
    """Bot ke tomar VC te anbe"""
    if not ctx.author.voice:
        await ctx.send("❌ Tumi kono VC te nai! Age VC te join koro")
        return
    
    channel = ctx.author.voice.channel
    try:
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"✅ Joined {channel.mention} | Ekhon kew join/leave korle ami voice e bolbo!")
        # Speak welcome
        await speak_in_vc(ctx.guild, f"Hello! Ami White Wolf bot, ekhon theke voice log bolbo", channel)
    except Exception as e:
        await ctx.send(f"❌ Join failed: {e}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    """Bot VC theke ber hobe"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 VC theke leave nilam")
    else:
        await ctx.send("❌ Ami kono VC te nai")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    """Bot ke diye voice e kichu bolabe - !say Hello world"""
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age !join diye VC te ano")
            return
    
    await ctx.send(f"🗣️ Bolchi: {text}")
    await speak_in_vc(ctx.guild, text, ctx.voice_client.channel)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong {round(bot.latency*1000)}ms | Voice TTS Bot 🐺")

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    """Test voice TTS"""
    if not ctx.author.voice:
        await ctx.send("❌ Age VC te join koro, tarpor !testvoice")
        return
    
    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()
    
    await ctx.send(f"🎙️ Testing voice in {channel.mention}...")
    await speak_in_vc(ctx.guild, f"Test successful! {ctx.author.display_name} voice test korse", channel)
    await speak_in_vc(ctx.guild, f"{ctx.author.display_name} voice e join korse", channel)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 WHITE_WOLF Voice TTS Bot", description="Bot VC te join hoye mukhe bolbe!", color=discord.Color.green())
    embed.add_field(name="🎙️ Auto", value="• Join korle VC te ese bolbe 'X join korse'\n• Leave nile bolbe 'X leave nise'\n• Move korle bolbe", inline=False)
    embed.add_field(name="💬 Commands", value="`!join` - Bot ke VC te ano\n`!leave` - Bot VC theke ber hobe\n`!say <text>` - Bot ke diye kichu bolao\n`!testvoice` - Voice test\n`!ping` - Ping check\n`!help` - Help", inline=False)
    embed.add_field(name="⚙️ Setup", value="1. `!join` diye bot ke VC te ano\n2. Kew join/leave korle bot auto bolbe\n3. Render e FFmpeg auto install hobe", inline=False)
    embed.set_footer(text="WHITE_WOLF GLOBAL • Voice TTS")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting Voice TTS Bot...", flush=True)
    bot.run(TOKEN)
