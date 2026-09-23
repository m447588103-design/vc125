"""
🐺 WHITE_WOLF Voice TTS Bot - FIXED VERSION
Fix: Auto-reconnect, FFmpeg check, better error handling, no instant disconnect
"""

import os
import asyncio
import threading
import time
import uuid
import shutil
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from gtts import gTTS

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))
VOICE_LANG = os.getenv('VOICE_LANG', 'bn')

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | LANG={VOICE_LANG}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# ========== CHECK FFMPEG ON STARTUP ==========
print("🔍 Checking FFmpeg...", flush=True)
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    print(f"✅ FFmpeg found at: {ffmpeg_path}", flush=True)
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        print(f"✅ FFmpeg version: {result.stdout.splitlines()[0]}", flush=True)
    except Exception as e:
        print(f"⚠️ FFmpeg version check failed: {e}", flush=True)
else:
    print("❌ FFmpeg NOT FOUND! Voice will NOT work!", flush=True)
    print("   -> Render buildCommand e 'apt-get install -y ffmpeg' thakte hobe", flush=True)

# ========== WEB SERVER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Voice TTS Bot Running')
        else:
            status = f"Bot Alive | FFmpeg: {bool(ffmpeg_path)} | Voice Ready"
            self.wfile.write(status.encode())
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

# ========== DISCORD ==========
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

speaking_locks = {}
# Track if bot should stay in VC
should_stay = {}

async def ensure_voice(guild, channel):
    """Bot ke VC te connect/reconnect korbe, disconnect hobe na"""
    try:
        vc = guild.voice_client
        if vc is None:
            print(f"🔊 Connecting to {channel.name} in {guild.name}", flush=True)
            vc = await channel.connect(timeout=10, self_deaf=False, self_mute=False)
            print(f"✅ Connected to {channel.name}", flush=True)
            should_stay[guild.id] = True
            return vc
        elif vc.channel.id != channel.id:
            print(f"🔄 Moving from {vc.channel.name} to {channel.name}", flush=True)
            await vc.move_to(channel)
            return vc
        else:
            # Already in correct channel
            if not vc.is_connected():
                print(f"⚠️ VC disconnected, reconnecting to {channel.name}", flush=True)
                try:
                    await vc.disconnect(force=True)
                except:
                    pass
                vc = await channel.connect(timeout=10)
            return vc
    except Exception as e:
        print(f"❌ ensure_voice failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

async def speak_text(guild, text, channel):
    """TTS generate + play with full error handling"""
    if guild.id not in speaking_locks:
        speaking_locks[guild.id] = asyncio.Lock()
    
    async with speaking_locks[guild.id]:
        vc = await ensure_voice(guild, channel)
        if not vc:
            print(f"❌ No VC to speak in {guild.name}", flush=True)
            return False

        # Check ffmpeg
        if not shutil.which("ffmpeg"):
            print("❌ FFmpeg not found, cannot play!", flush=True)
            return False

        filename = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
        try:
            # TTS Generation
            lang = VOICE_LANG
            # If Bangla chars, use bn
            if any('\u0980' <= c <= '\u09FF' for c in text):
                lang = 'bn'
            
            print(f"🗣️ Generating TTS: '{text}' lang={lang}", flush=True)
            try:
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(filename)
                print(f"✅ TTS saved: {filename} ({os.path.getsize(filename)} bytes)", flush=True)
            except Exception as e:
                print(f"⚠️ gTTS {lang} failed: {e}, trying en", flush=True)
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(filename)
                print(f"✅ TTS fallback saved", flush=True)

            # Play
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                print(f"❌ TTS file empty or missing!", flush=True)
                return False

            # Stop if already playing
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)

            print(f"▶️ Playing in {vc.channel.name}: {text}", flush=True)
            source = discord.FFmpegPCMAudio(filename, options='-vn -loglevel quiet')
            vc.play(source)

            # Wait with timeout (max 15 sec per message)
            timeout = 15
            start = time.time()
            while vc.is_playing() and (time.time() - start) < timeout:
                await asyncio.sleep(0.5)
            
            if vc.is_playing():
                print(f"⚠️ Play timeout, stopping", flush=True)
                vc.stop()
            
            print(f"✅ Done speaking: {text}", flush=True)
            return True

        except Exception as e:
            print(f"❌ speak_text error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
        finally:
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except:
                pass

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 VOICE TTS BOT ONLINE! {bot.user}\nFFmpeg: {bool(ffmpeg_path)} | Guilds: {len(bot.guilds)}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!join | Voice TTS"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            # JOIN
            text = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text}", flush=True)
            # Small delay so Discord VC fully ready
            await asyncio.sleep(1)
            await speak_text(member.guild, text, after.channel)

        elif before.channel is not None and after.channel is None:
            # LEAVE
            text = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text}", flush=True)
            
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await speak_text(member.guild, text, before.channel)
                # Don't disconnect instantly - wait 30s, if empty then leave
                await asyncio.sleep(3)
                # Check if only bot left
                if len(before.channel.members) == 1 and before.channel.members[0].id == bot.user.id:
                    print(f"   -> Channel empty, will stay 30s then leave", flush=True)
                    await asyncio.sleep(30)
                    # Check again
                    if len(before.channel.members) == 1:
                        try:
                            await vc.disconnect()
                            print(f"   -> Left empty channel {before.channel.name}", flush=True)
                            should_stay.pop(member.guild.id, None)
                        except:
                            pass
            else:
                # Bot not in that channel, don't speak for leave
                print(f"   -> Bot not in {before.channel.name}, skip leave announcement", flush=True)

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text}", flush=True)
            await asyncio.sleep(1)
            await speak_text(member.guild, text, after.channel)

    except Exception as e:
        print(f"❌ Voice event error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# ========== COMMANDS ==========
@bot.command(name="join")
async def join_cmd(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Age VC te join koro!")
        return
    ch = ctx.author.voice.channel
    try:
        vc = await ensure_voice(ctx.guild, ch)
        if vc:
            await ctx.send(f"✅ Joined {ch.mention} | Ekhon kew join/leave korle bolbo! FFmpeg: {bool(ffmpeg_path)}")
            await asyncio.sleep(1)
            await speak_text(ctx.guild, f"Hello! Ami White Wolf bot, voice log bolbo", ch)
        else:
            await ctx.send("❌ VC join failed!")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        should_stay.pop(ctx.guild.id, None)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Leave nilam")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ensure_voice(ctx.guild, ctx.author.voice.channel)
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ {text}")
    await speak_text(ctx.guild, text, ctx.voice_client.channel)

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ VC te join koro age")
        return
    ch = ctx.author.voice.channel
    await ensure_voice(ctx.guild, ch)
    await ctx.send(f"🎙️ Testing in {ch.mention} | FFmpeg: {ffmpeg_path}")
    await speak_text(ctx.guild, f"Test successful! {ctx.author.display_name} voice test", ch)
    await asyncio.sleep(1)
    await speak_text(ctx.guild, f"{ctx.author.display_name} voice e join korse", ch)

@bot.command(name="ffmpegcheck")
async def ffmpegcheck_cmd(ctx):
    path = shutil.which("ffmpeg")
    if path:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            ver = r.stdout.splitlines()[0]
            await ctx.send(f"✅ FFmpeg OK: {path}\n{ver}")
        except Exception as e:
            await ctx.send(f"⚠️ FFmpeg found at {path} but version check failed: {e}")
    else:
        await ctx.send("❌ FFmpeg NOT FOUND! Render buildCommand e `apt-get install -y ffmpeg` add koro")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(ffmpeg_path)} | VC: {bool(ctx.voice_client)}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 Voice TTS Bot - Fixed", color=discord.Color.green())
    embed.add_field(name="Auto", value="Join/Leave/Move bolbe voice e", inline=False)
    embed.add_field(name="Commands", value="`!join` `!leave` `!say <text>` `!testvoice` `!ffmpegcheck` `!ping`", inline=False)
    embed.add_field(name="Fix", value="FFmpeg check + auto-reconnect + no instant disconnect", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting Voice TTS Bot - Fixed Version...", flush=True)
    bot.run(TOKEN)
