"""
🐺 WHITE_WOLF Voice TTS Bot - NO APT-GET NEEDED!
imageio-ffmpeg diye pip diyei FFmpeg install hobe
Render e 100% host hobe apt-get chara
"""

import os
import asyncio
import threading
import time
import uuid
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from gtts import gTTS

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNEL_ID')
if NOTIFICATION_CHANNEL_ID:
    try:
        NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID)
    except:
        NOTIFICATION_CHANNEL_ID = None

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# ========== FFMPEG SETUP - NO APT NEEDED ==========
# imageio-ffmpeg pip package diye FFmpeg binary auto install hobe
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg via imageio-ffmpeg: {FFMPEG_EXE}", flush=True)
    print(f"   Exists: {os.path.exists(FFMPEG_EXE)}", flush=True)
except Exception as e:
    print(f"⚠️ imageio-ffmpeg not found: {e}", flush=True)
    # Fallback to system ffmpeg
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"   System FFmpeg: {FFMPEG_EXE}", flush=True)

if not FFMPEG_EXE:
    print("❌ FFmpeg NOT FOUND! Voice may not work", flush=True)
else:
    print(f"✅ Using FFmpeg: {FFMPEG_EXE}", flush=True)

# Check Opus
try:
    if not discord.opus.is_loaded():
        for lib in ['libopus.so.0', 'libopus.so', 'libopus.so.1', 'opus']:
            try:
                discord.opus.load_opus(lib)
                if discord.opus.is_loaded():
                    print(f"✅ Opus loaded: {lib}", flush=True)
                    break
            except:
                continue
    print(f"Opus loaded: {discord.opus.is_loaded()}", flush=True)
except Exception as e:
    print(f"⚠️ Opus check: {e}", flush=True)

# ========== WEB SERVER FOR RENDER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - TTS Bot Running')
        else:
            self.wfile.write(b'WHITE_WOLF TTS Bot Alive - No apt-get needed')
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Web server on 0.0.0.0:{PORT}...", flush=True)
        httpd = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ WEB LISTENING on 0.0.0.0:{PORT}", flush=True)
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

voice_lock = asyncio.Lock()

async def tts_speak(guild, channel, text):
    """TTS - gTTS + FFmpeg (imageio-ffmpeg binary)"""
    async with voice_lock:
        try:
            vc = guild.voice_client
            if vc is None:
                print(f"🔊 Joining {channel.name} to speak: {text}", flush=True)
                vc = await channel.connect()
            elif vc.channel.id != channel.id:
                print(f"🔄 Moving to {channel.name}", flush=True)
                await vc.move_to(channel)
            
            tmp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
            print(f"🗣️ gTTS: '{text}' -> {tmp_file}", flush=True)
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(tmp_file)
            
            print(f"✅ TTS saved {os.path.getsize(tmp_file)} bytes", flush=True)
            
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)
            
            print(f"▶️ Playing in {channel.name}: {text}", flush=True)
            
            # Use imageio-ffmpeg binary if available
            if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
                source = discord.FFmpegPCMAudio(tmp_file, executable=FFMPEG_EXE, options='-vn -loglevel quiet')
            else:
                source = discord.FFmpegPCMAudio(tmp_file, options='-vn -loglevel quiet')
            
            vc.play(source)
            
            while vc.is_playing():
                await asyncio.sleep(0.5)
            
            print(f"✅ Done: {text}", flush=True)
            
            try:
                os.remove(tmp_file)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ TTS Error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                if 'tmp_file' in locals() and os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except:
                pass
            return False

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 TTS BOT ONLINE! {bot.user}\nFFmpeg: {FFMPEG_EXE}\nOpus: {discord.opus.is_loaded()}\nGuilds: {len(bot.guilds)}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Voice TTS | !join"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            text = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text)
            
            if NOTIFICATION_CHANNEL_ID:
                try:
                    ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                    embed = discord.Embed(title="🎙️ Joined", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
                    await ch.send(embed=embed)
                except:
                    pass

        elif before.channel is not None and after.channel is None:
            text = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text}", flush=True)
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await tts_speak(member.guild, before.channel, text)
                await asyncio.sleep(2)
                if len(before.channel.members) == 1:
                    await asyncio.sleep(8)
                    if len(before.channel.members) == 1:
                        try:
                            await vc.disconnect()
                        except:
                            pass
            
            if NOTIFICATION_CHANNEL_ID:
                try:
                    ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                    embed = discord.Embed(title="👋 Left", description=f"**{member.display_name}** left **{before.channel.name}**", color=discord.Color.red())
                    await ch.send(embed=embed)
                except:
                    pass

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text)

    except Exception as e:
        print(f"❌ Voice event error: {e}", flush=True)
        import traceback
        traceback.print_exc()

@bot.command(name="join")
async def join_cmd(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Age VC te join koro!")
        return
    ch = ctx.author.voice.channel
    perms = ch.permissions_for(ctx.guild.me)
    if not perms.connect or not perms.speak:
        await ctx.send(f"❌ {ch.mention} e Connect+Speak permission nai!")
        return
    try:
        vc = ctx.guild.voice_client
        if vc:
            if vc.channel.id == ch.id:
                await ctx.send(f"✅ Already in {ch.mention}")
                return
            await vc.move_to(ch)
            await ctx.send(f"✅ Moved to {ch.mention}")
        else:
            await ch.connect()
            await ctx.send(f"✅ Joined {ch.mention} | FFmpeg: {bool(FFMPEG_EXE)} | Ekhon `!testvoice` likho")
    except Exception as e:
        await ctx.send(f"❌ Join fail: {e}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ Bolchi: {text}")
    await tts_speak(ctx.guild, ctx.voice_client.channel, text)

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age VC te join koro, tarpor !join")
            return
    await ctx.send("🎙️ Testing TTS...")
    await tts_speak(ctx.guild, ctx.voice_client.channel, f"{ctx.author.display_name} voice e join korse")
    await ctx.send("✅ Jodi sunte paiso, TTS kaj kore!")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(FFMPEG_EXE)} | Opus: {discord.opus.is_loaded()}")

@bot.command(name="debug")
async def debug_cmd(ctx):
    vc = ctx.voice_client
    await ctx.send(f"""
**DEBUG**
Bot VC: {vc.channel.name if vc else 'None'}
FFmpeg: {FFMPEG_EXE or 'NOT FOUND'}
Opus: {discord.opus.is_loaded()}
""")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 TTS Voice Bot - No apt-get", color=discord.Color.green())
    embed.add_field(name="Auto", value="Join/Leave/Move voice e bolbe", inline=False)
    embed.add_field(name="Commands", value="`!join` `!leave` `!say <text>` `!testvoice`", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting TTS Bot - No apt-get needed...", flush=True)
    bot.run(TOKEN)
