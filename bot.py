"""
🐺 WHITE_WOLF VOICE TTS FINAL - SOUND DIYE BOLBE!
Kew join korle bot VC te join hoye SOUND diye bolbe "X join korse"
Render 100% Working - FFmpeg + gTTS + Local Beep Fallback
"""

import os
import asyncio
import threading
import time
import uuid
import shutil
import subprocess
import wave
import struct
import math
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

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | TEXT_FALLBACK={NOTIFICATION_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# ========== CHECK DEPS ==========
print("🔍 Checking FFmpeg, Opus, PyNaCl...", flush=True)
ffmpeg_path = shutil.which("ffmpeg")
print(f"FFmpeg: {ffmpeg_path}", flush=True)
if ffmpeg_path:
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        print(f"✅ {r.stdout.splitlines()[0]}", flush=True)
    except Exception as e:
        print(f"⚠️ FFmpeg check fail: {e}", flush=True)
else:
    print("❌ FFmpeg NOT FOUND - Voice won't work!", flush=True)

try:
    import nacl
    print(f"✅ PyNaCl {nacl.__version__}", flush=True)
except Exception as e:
    print(f"❌ PyNaCl missing: {e}", flush=True)

# Load Opus - try all possible names
opus_loaded = False
for lib in ['libopus.so.0', 'libopus.so', 'libopus.so.1', 'opus', 'libopus']:
    try:
        if not discord.opus.is_loaded():
            discord.opus.load_opus(lib)
        if discord.opus.is_loaded():
            print(f"✅ Opus loaded: {lib}", flush=True)
            opus_loaded = True
            break
    except:
        continue

if not discord.opus.is_loaded():
    print("❌ Opus NOT loaded - trying auto load", flush=True)
    try:
        # discord.py will try to load automatically
        pass
    except:
        pass
print(f"Opus loaded: {discord.opus.is_loaded()}", flush=True)

# ========== CREATE LOCAL TEST SOUND (Beep) FOR VOICE TEST WITHOUT TTS ==========
def create_beep(filename, duration=1.0, freq=440):
    """Create a simple beep wav file - no internet needed, 100% works"""
    try:
        sample_rate = 48000
        n_samples = int(sample_rate * duration)
        with wave.open(filename, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_samples):
                # Simple sine wave beep
                value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
                wav.writeframes(struct.pack('<h', value))
        print(f"✅ Beep created: {filename}", flush=True)
        return True
    except Exception as e:
        print(f"❌ Beep create fail: {e}", flush=True)
        return False

BEEP_FILE = "/tmp/beep.wav"
create_beep(BEEP_FILE, duration=0.8, freq=600)

# ========== WEB SERVER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Voice TTS Bot')
        else:
            self.wfile.write(f"Voice TTS Bot | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}".encode())
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Web on 0.0.0.0:{PORT}", flush=True)
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

voice_locks = {}

async def get_voice_client(guild, channel):
    """Ensure bot in VC, with auto-reconnect"""
    try:
        vc = guild.voice_client
        if vc is None:
            print(f"🔊 Connecting to {channel.name}", flush=True)
            vc = await channel.connect(timeout=15, self_deaf=False, self_mute=False)
            print(f"✅ Connected to {channel.name}", flush=True)
            return vc
        elif vc.channel.id != channel.id:
            print(f"🔄 Moving to {channel.name}", flush=True)
            await vc.move_to(channel)
            return vc
        else:
            if not vc.is_connected():
                print(f"⚠️ VC disconnected, reconnecting...", flush=True)
                try:
                    await vc.disconnect(force=True)
                except:
                    pass
                vc = await channel.connect(timeout=15)
            return vc
    except Exception as e:
        print(f"❌ get_voice_client fail: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

async def play_sound(guild, channel, text=None, use_beep=False):
    """
    Voice e sound bajabe
    - use_beep=True hole local beep bajabe (100% works, no internet)
    - text dile gTTS diye bolbe
    """
    gid = guild.id
    if gid not in voice_locks:
        voice_locks[gid] = asyncio.Lock()
    
    async with voice_locks[gid]:
        vc = await get_voice_client(guild, channel)
        if not vc:
            print(f"❌ No VC for {guild.name}", flush=True)
            return False

        if not ffmpeg_path:
            print("❌ FFmpeg not found, cannot play sound", flush=True)
            return False

        if not discord.opus.is_loaded():
            print("❌ Opus not loaded, cannot play", flush=True)
            return False

        temp_file = None
        try:
            if use_beep:
                # Play local beep - 100% works
                print(f"🔔 Playing BEEP in {channel.name}", flush=True)
                source = discord.FFmpegPCMAudio(BEEP_FILE, options='-vn -loglevel quiet')
            else:
                # TTS
                if not text:
                    return False
                
                temp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
                print(f"🗣️ TTS: '{text}' -> {temp_file}", flush=True)
                
                try:
                    # Try Bangla first if Bangla chars, else English
                    lang = 'bn' if any('\u0980' <= c <= '\u09FF' for c in text) else 'en'
                    # User wants Bangla: "join korse" - use en for mixed, bn for pure Bangla
                    # For "X join korse" mixed, en works better
                    if 'join korse' in text or 'leave nise' in text or 'move korse' in text:
                        lang = 'bn'  # Try bn for Bangla phrases
                    
                    tts = gTTS(text=text, lang=lang, slow=False)
                    tts.save(temp_file)
                    print(f"✅ TTS saved {os.path.getsize(temp_file)} bytes lang={lang}", flush=True)
                except Exception as e:
                    print(f"⚠️ gTTS {lang} fail: {e}, trying en", flush=True)
                    try:
                        tts = gTTS(text=text, lang='en', slow=False)
                        tts.save(temp_file)
                        print(f"✅ TTS fallback en saved", flush=True)
                    except Exception as e2:
                        print(f"❌ gTTS fallback fail: {e2}, using beep", flush=True)
                        # Fallback to beep if TTS fails
                        source = discord.FFmpegPCMAudio(BEEP_FILE, options='-vn')
                        if vc.is_playing():
                            vc.stop()
                        vc.play(source)
                        while vc.is_playing():
                            await asyncio.sleep(0.5)
                        return True

                if not os.path.exists(temp_file) or os.path.getsize(temp_file) < 100:
                    print(f"❌ TTS file invalid", flush=True)
                    return False

                source = discord.FFmpegPCMAudio(temp_file, options='-vn -loglevel quiet')

            # Play
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.3)

            print(f"▶️ Playing in {vc.channel.name}", flush=True)
            vc.play(source)

            # Wait max 10 sec
            start = time.time()
            while vc.is_playing() and (time.time() - start) < 10:
                await asyncio.sleep(0.3)
            
            if vc.is_playing():
                vc.stop()
            
            print(f"✅ Played successfully", flush=True)
            return True

        except Exception as e:
            print(f"❌ play_sound error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 VOICE TTS BOT ONLINE! {bot.user}\nFFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!join | Voice e bolbo"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        if member.id == bot.user.id:
            if before.channel is None and after.channel is not None:
                print(f"🤖 BOT JOINED {after.channel.name}", flush=True)
            elif before.channel is None and after.channel is None:
                pass
            elif before.channel is not None and after.channel is None:
                print(f"🤖 BOT LEFT {before.channel.name}", flush=True)
        return

    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            # JOIN - Bot VC te join hoye bolbe
            text = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text} in {after.channel.name}", flush=True)
            await asyncio.sleep(1)  # Let user fully join
            success = await play_sound(member.guild, after.channel, text=text)
            
            # Text fallback
            if not success and NOTIFICATION_CHANNEL_ID:
                try:
                    ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                    await ch.send(f"🎙️ **{member.display_name}** joined **{after.channel.name}** (Voice play failed, text fallback)")
                except:
                    pass

        elif before.channel is not None and after.channel is None:
            # LEAVE
            text = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text}", flush=True)
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await play_sound(member.guild, before.channel, text=text)
                # Stay 15 sec then leave if empty
                await asyncio.sleep(3)
                if len(before.channel.members) == 1:
                    await asyncio.sleep(12)
                    if len(before.channel.members) == 1:
                        try:
                            await vc.disconnect()
                            print(f"   -> Left empty {before.channel.name}", flush=True)
                        except:
                            pass
            # Text fallback
            if NOTIFICATION_CHANNEL_ID:
                try:
                    ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                    await ch.send(f"👋 **{member.display_name}** left **{before.channel.name}**")
                except:
                    pass

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text}", flush=True)
            await asyncio.sleep(1)
            await play_sound(member.guild, after.channel, text=text)

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
    perms = ch.permissions_for(ctx.guild.me)
    if not perms.connect or not perms.speak:
        await ctx.send(f"❌ Permission nai! {ch.mention} e Connect+Speak dao")
        return
    
    print(f"🔊 !join {ch.name} by {ctx.author}", flush=True)
    try:
        vc = await get_voice_client(ctx.guild, ch)
        if vc:
            await ctx.send(f"✅ Joined {ch.mention}\nFFmpeg: {bool(ffmpeg_path)}\nOpus: {discord.opus.is_loaded()}\n\nEkhon `!beep` diye sound test koro, tarpor `!testvoice`")
        else:
            await ctx.send("❌ Join failed, check logs")
    except Exception as e:
        await ctx.send(f"❌ {e}")
        import traceback
        traceback.print_exc()

@bot.command(name="beep")
async def beep_cmd(ctx):
    """Local beep sound test - no internet needed, 100% works if FFmpeg ok"""
    if not ctx.voice_client:
        if ctx.author.voice:
            await get_voice_client(ctx.guild, ctx.author.voice.channel)
        else:
            await ctx.send("❌ Age !join")
            return
    
    await ctx.send("🔔 Beep bajacchi... (Local file, no TTS)")
    success = await play_sound(ctx.guild, ctx.voice_client.channel, use_beep=True)
    if success:
        await ctx.send("✅ Beep bajse! Voice kaj kore, TTS issue hole beep diye fallback korbo")
    else:
        await ctx.send("❌ Beep o bajlo na! FFmpeg/Opus problem")

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            await get_voice_client(ctx.guild, ctx.author.voice.channel)
        else:
            await ctx.send("❌ Age !join")
            return
    
    await ctx.send(f"🎙️ Testing TTS voice...")
    # Test 1: Beep
    await play_sound(ctx.guild, ctx.voice_client.channel, use_beep=True)
    await asyncio.sleep(1)
    # Test 2: TTS
    await ctx.send(f"🗣️ Ekhon TTS bolbo: '{ctx.author.display_name} voice e join korse'")
    success = await play_sound(ctx.guild, ctx.voice_client.channel, text=f"{ctx.author.display_name} voice e join korse")
    if success:
        await ctx.send("✅ TTS kaj korse! Ekhon auto join/leave bolbe")
    else:
        await ctx.send("❌ TTS fail, kintu beep kaj korle voice thik ache, gTTS internet issue")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await get_voice_client(ctx.guild, ctx.author.voice.channel)
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ Bolchi: {text}")
    await play_sound(ctx.guild, ctx.voice_client.channel, text=text)

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="debug")
async def debug_cmd(ctx):
    vc = ctx.voice_client
    user_vc = ctx.author.voice.channel if ctx.author.voice else None
    perms = user_vc.permissions_for(ctx.guild.me) if user_vc else None
    await ctx.send(f"""
**DEBUG**
You VC: {user_vc.name if user_vc else 'None'}
Bot VC: {vc.channel.name if vc else 'None'} | Connected: {vc.is_connected() if vc else False}
Perms: Connect={perms.connect if perms else 'N/A'} Speak={perms.speak if perms else 'N/A'}
FFmpeg: {ffmpeg_path or 'NOT FOUND'}
Opus: {discord.opus.is_loaded()}
Beep file: {os.path.exists(BEEP_FILE)}
""")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 Voice TTS Bot - Sound diye bolbe!", color=discord.Color.green())
    embed.add_field(name="🎙️ Auto", value="Join korle VC te ese bolbe 'X join korse'\nLeave nile 'X leave nise'", inline=False)
    embed.add_field(name="Commands", value="`!join` - VC te ano\n`!beep` - Beep test (100% works)\n`!testvoice` - TTS test\n`!say <text>` - Kichu bolao\n`!leave` - Leave\n`!debug` - Debug", inline=False)
    embed.add_field(name="Fix", value="1. `!join` 2. `!beep` 3. `!testvoice` - step by step test koro", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting VOICE TTS Bot - Sound diye bolbe...", flush=True)
    bot.run(TOKEN)
