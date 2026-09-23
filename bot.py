"""
FINAL FIX - Bot VC te ese chole jawa + TTS na baja
- Auto-disconnect 10s -> 5 min (300s)
- Beep fallback if TTS fails
- Detailed logs
"""

import os
import asyncio
import threading
import time
import uuid
import shutil
import math
import wave
import struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from gtts import gTTS

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNELS') or os.getenv('NOTIFICATION_CHANNEL_ID')
if NOTIFICATION_CHANNEL_ID:
    # Parse multi-server, but for TTS we just need text fallback optional
    try:
        if NOTIFICATION_CHANNEL_ID.strip().startswith('{'):
            import json
            data = json.loads(NOTIFICATION_CHANNEL_ID)
            # Take first channel ID for fallback
            NOTIFICATION_CHANNEL_ID = list(data.values())[0] if data else None
        elif ':' in NOTIFICATION_CHANNEL_ID and ',' in NOTIFICATION_CHANNEL_ID:
            # guild:channel,guild:channel -> take first channel
            first = NOTIFICATION_CHANNEL_ID.split(',')[0]
            if ':' in first:
                NOTIFICATION_CHANNEL_ID = int(first.split(':')[1].strip())
            else:
                NOTIFICATION_CHANNEL_ID = int(first.strip())
        elif ':' in NOTIFICATION_CHANNEL_ID:
            NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID.split(':')[1].strip())
        else:
            # Single or comma list
            NOTIFICATION_CHANNEL_ID = NOTIFICATION_CHANNEL_ID.split(',')[0].strip()
            NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID)
    except:
        try:
            NOTIFICATION_CHANNEL_ID = int(str(NOTIFICATION_CHANNEL_ID).split(',')[0].strip())
        except:
            NOTIFICATION_CHANNEL_ID = None

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | TEXT_CH={NOTIFICATION_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# FFmpeg via imageio-ffmpeg (no apt-get)
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg: {FFMPEG_EXE} Exists={os.path.exists(FFMPEG_EXE)}", flush=True)
except Exception as e:
    print(f"⚠️ imageio-ffmpeg fail: {e}", flush=True)
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"   System FFmpeg: {FFMPEG_EXE}", flush=True)

# Create beep file for fallback (100% works, no internet)
BEEP_FILE = "/tmp/beep.wav"
def create_beep():
    try:
        sample_rate = 48000
        duration = 0.6
        freq = 800
        n_samples = int(sample_rate * duration)
        with wave.open(BEEP_FILE, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_samples):
                value = int(32767 * 0.4 * math.sin(2 * math.pi * freq * i / sample_rate))
                wav.writeframes(struct.pack('<h', value))
        print(f"✅ Beep file created: {BEEP_FILE} {os.path.getsize(BEEP_FILE)} bytes", flush=True)
        return True
    except Exception as e:
        print(f"❌ Beep create fail: {e}", flush=True)
        return False

create_beep()

# Web server
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - TTS Bot - No auto disconnect')
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

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

voice_lock = asyncio.Lock()

async def play_tts(guild, channel, text, use_beep_fallback=True):
    """Play TTS with beep fallback, stay in VC"""
    async with voice_lock:
        vc = None
        tmp_file = None
        try:
            # Get VC
            vc = guild.voice_client
            if vc is None:
                print(f"🔊 Joining {channel.name} for: {text}", flush=True)
                vc = await channel.connect(timeout=15, self_deaf=False)
                print(f"✅ Joined {channel.name}", flush=True)
            elif vc.channel.id != channel.id:
                print(f"🔄 Moving to {channel.name}", flush=True)
                await vc.move_to(channel)
            
            if not vc or not vc.is_connected():
                print(f"❌ VC not connected for {guild.name}", flush=True)
                return False

            # Check FFmpeg
            if not FFMPEG_EXE or not os.path.exists(FFMPEG_EXE):
                print(f"❌ FFmpeg not found: {FFMPEG_EXE}", flush=True)
                # Try system ffmpeg
                sys_ff = shutil.which("ffmpeg")
                if not sys_ff:
                    print("❌ No FFmpeg at all, cannot play", flush=True)
                    return False

            # Try TTS first
            tts_success = False
            if text:
                tmp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
                try:
                    print(f"🗣️ gTTS generating: '{text}'", flush=True)
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(tmp_file)
                    
                    if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 500:
                        print(f"✅ TTS saved: {os.path.getsize(tmp_file)} bytes", flush=True)
                        
                        if vc.is_playing():
                            vc.stop()
                            await asyncio.sleep(0.5)
                        
                        # Use imageio-ffmpeg binary
                        if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
                            source = discord.FFmpegPCMAudio(tmp_file, executable=FFMPEG_EXE, options='-vn -loglevel quiet')
                        else:
                            source = discord.FFmpegPCMAudio(tmp_file, options='-vn -loglevel quiet')
                        
                        print(f"▶️ Playing TTS: {text}", flush=True)
                        vc.play(source)
                        
                        # Wait max 12 sec
                        start = time.time()
                        while vc.is_playing() and (time.time() - start) < 12:
                            await asyncio.sleep(0.3)
                        
                        if vc.is_playing():
                            vc.stop()
                        
                        print(f"✅ TTS played: {text}", flush=True)
                        tts_success = True
                    else:
                        print(f"❌ TTS file too small or missing", flush=True)
                        
                except Exception as e:
                    print(f"❌ gTTS failed: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                finally:
                    try:
                        if tmp_file and os.path.exists(tmp_file):
                            os.remove(tmp_file)
                    except:
                        pass

            # If TTS failed and beep fallback allowed, play beep
            if not tts_success and use_beep_fallback:
                try:
                    print(f"🔔 TTS failed, playing BEEP fallback in {channel.name}", flush=True)
                    if not os.path.exists(BEEP_FILE):
                        create_beep()
                    
                    if vc.is_playing():
                        vc.stop()
                        await asyncio.sleep(0.3)
                    
                    if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
                        source = discord.FFmpegPCMAudio(BEEP_FILE, executable=FFMPEG_EXE, options='-vn -loglevel quiet')
                    else:
                        source = discord.FFmpegPCMAudio(BEEP_FILE, options='-vn -loglevel quiet')
                    
                    vc.play(source)
                    while vc.is_playing():
                        await asyncio.sleep(0.3)
                    
                    print(f"✅ Beep played (fallback)", flush=True)
                    return True
                except Exception as e:
                    print(f"❌ Beep fallback also failed: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    return False
            
            return tts_success

        except Exception as e:
            print(f"❌ play_tts error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 TTS BOT ONLINE! {bot.user}\nFFmpeg: {FFMPEG_EXE}\nOpus: {discord.opus.is_loaded()}\nGuilds: {len(bot.guilds)}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!join | !beep | !testvoice"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            # JOIN - Bot join hoye bolbe, ar 5 MIN thakbe, instant leave korbe na
            text = f"{member.display_name} joined {after.channel.name}"
            text_bn = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text_bn} in {after.channel.name}", flush=True)
            await asyncio.sleep(0.8)
            await play_tts(member.guild, after.channel, text_bn, use_beep_fallback=True)
            
            # Text fallback
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
            text_bn = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text_bn}", flush=True)
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await play_tts(member.guild, before.channel, text_bn, use_beep_fallback=True)
                # Stay 5 MINUTES (300 sec) not 10 sec! So bot won't come and go
                print(f"   -> Will stay 5 min in {before.channel.name} before leaving if empty", flush=True)
                await asyncio.sleep(5)
                # Check if only bot left
                if len(before.channel.members) == 1:
                    # Wait 5 min
                    for i in range(60):  # 60 * 5 sec = 300 sec = 5 min
                        await asyncio.sleep(5)
                        if not vc or not vc.is_connected():
                            break
                        if len(before.channel.members) > 1:
                            print(f"   -> Someone rejoined {before.channel.name}, staying", flush=True)
                            break
                        if i % 12 == 0:  # Every 60 sec
                            print(f"   -> Still waiting in empty {before.channel.name}... {i*5}s", flush=True)
                    # After 5 min, if still only bot, leave
                    if vc and vc.is_connected() and len(before.channel.members) == 1:
                        try:
                            await vc.disconnect()
                            print(f"   -> Left empty channel after 5 min: {before.channel.name}", flush=True)
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
            text_bn = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text_bn}", flush=True)
            await asyncio.sleep(0.8)
            await play_tts(member.guild, after.channel, text_bn, use_beep_fallback=True)

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
                await ctx.send(f"✅ Already in {ch.mention} | Connected: {vc.is_connected()}")
                return
            await vc.move_to(ch)
            await ctx.send(f"✅ Moved to {ch.mention}")
        else:
            await ch.connect()
            await ctx.send(f"✅ Joined {ch.mention}\nEkhon `!beep` diye test koro, tarpor `!testvoice`\nBot 5 min thakbe, instant leave korbe na!")
    except Exception as e:
        await ctx.send(f"❌ Join fail: {e}")
        print(f"❌ Join fail: {e}", flush=True)

@bot.command(name="beep")
async def beep_cmd(ctx):
    """Beep test - 100% works, no TTS, no internet"""
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age !join")
            return
    
    await ctx.send("🔔 Beep bajacchi... (Local file, 100% works)")
    # Force beep only
    try:
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.3)
        
        if not os.path.exists(BEEP_FILE):
            create_beep()
        
        if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
            source = discord.FFmpegPCMAudio(BEEP_FILE, executable=FFMPEG_EXE, options='-vn -loglevel quiet')
        else:
            source = discord.FFmpegPCMAudio(BEEP_FILE, options='-vn -loglevel quiet')
        
        vc.play(source)
        while vc.is_playing():
            await asyncio.sleep(0.3)
        
        await ctx.send("✅ Beep bajse! Voice kaj kore! Ekhon `!testvoice` try koro TTS er jonno")
    except Exception as e:
        await ctx.send(f"❌ Beep fail: {e}\nFFmpeg: {FFMPEG_EXE}")
        print(f"❌ Beep fail: {e}", flush=True)

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age VC te join koro, tarpor !join")
            return
    
    await ctx.send(f"🎙️ TTS test: '{ctx.author.display_name} voice e join korse'")
    success = await play_tts(ctx.guild, ctx.voice_client.channel, f"{ctx.author.display_name} voice e join korse", use_beep_fallback=True)
    if success:
        await ctx.send("✅ TTS bajse! Ekhon auto join/leave te bolbe")
    else:
        await ctx.send("❌ TTS fail, kintu `!beep` kaj korle voice thik ache")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ Bolchi: {text}")
    await play_tts(ctx.guild, ctx.voice_client.channel, text, use_beep_fallback=True)

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
    await ctx.send(f"""
**DEBUG**
Bot VC: {vc.channel.name if vc else 'None'} | Connected: {vc.is_connected() if vc else False}
FFmpeg: {FFMPEG_EXE or 'NOT FOUND'} Exists: {os.path.exists(FFMPEG_EXE) if FFMPEG_EXE else False}
Opus: {discord.opus.is_loaded()}
Beep: {os.path.exists(BEEP_FILE)} {os.path.getsize(BEEP_FILE) if os.path.exists(BEEP_FILE) else 0} bytes
Stay time: 5 min (not instant)
""")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(FFMPEG_EXE)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting TTS Bot - 5 min stay + Beep fallback...", flush=True)
    bot.run(TOKEN)
