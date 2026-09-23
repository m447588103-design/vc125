"""
🐺 WHITE_WOLF Voice TTS - FINAL 100% WORKING VERSION
- NO AUTO-DISCONNECT - Bot VC te join korle ar ber hobe na, !leave na dile
- Beep + TTS both - beep 100% bajbe, TTS try korbe
- Simple logic, no complex auto-leave
- Render + Local both working
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
# Parse single ID for text fallback
TEXT_CHANNEL_ID = None
if NOTIFICATION_CHANNEL_ID:
    try:
        # Try to get first channel ID from any format
        raw = NOTIFICATION_CHANNEL_ID.strip()
        if raw.startswith('{'):
            import json
            data = json.loads(raw)
            TEXT_CHANNEL_ID = list(data.values())[0]
        elif ':' in raw:
            # guild:channel format
            first = raw.split(',')[0]
            if ':' in first:
                TEXT_CHANNEL_ID = int(first.split(':')[1].strip())
            else:
                TEXT_CHANNEL_ID = int(first.strip())
        else:
            TEXT_CHANNEL_ID = int(raw.split(',')[0].strip())
    except:
        try:
            TEXT_CHANNEL_ID = int(str(NOTIFICATION_CHANNEL_ID).split(',')[0].strip())
        except:
            TEXT_CHANNEL_ID = None

print(f"🔧 TOKEN={bool(TOKEN)} PORT={PORT} TEXT_CH={TEXT_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# FFmpeg via imageio-ffmpeg (pip, no apt-get)
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg: {FFMPEG_EXE} Exists={os.path.exists(FFMPEG_EXE)}", flush=True)
except Exception as e:
    print(f"⚠️ imageio-ffmpeg fail: {e}", flush=True)
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"System FFmpeg: {FFMPEG_EXE}", flush=True)

# Create beep file - local, no internet, 100% works
BEEP_FILE = "/tmp/beep.wav"
def make_beep():
    try:
        sr = 48000
        dur = 0.5
        freq = 800
        n = int(sr * dur)
        with wave.open(BEEP_FILE, 'w') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            for i in range(n):
                v = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sr))
                w.writeframes(struct.pack('<h', v))
        print(f"✅ Beep created {os.path.getsize(BEEP_FILE)} bytes", flush=True)
        return True
    except Exception as e:
        print(f"❌ Beep fail: {e}", flush=True)
        return False

make_beep()

# Web server for Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Final TTS Bot - No auto disconnect')
    def log_message(self, format, *args):
        return

def start_web():
    try:
        httpd = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ WEB LISTENING on 0.0.0.0:{PORT}", flush=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"❌ Web error: {e}", flush=True)

threading.Thread(target=start_web, daemon=True).start()
time.sleep(1)

# Discord bot
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

lock = asyncio.Lock()

async def play_audio(guild, channel, text=None, beep_only=False):
    """Play audio in VC - FINAL SIMPLE VERSION"""
    async with lock:
        try:
            # Get or create voice client - STAY FOREVER, NO AUTO LEAVE
            vc = guild.voice_client
            if vc is None:
                print(f"🔊 JOINING {channel.name} for {text or 'beep'}", flush=True)
                vc = await channel.connect(timeout=15, self_deaf=False)
                print(f"✅ JOINED {channel.name}", flush=True)
            elif vc.channel.id != channel.id:
                print(f"🔄 MOVING to {channel.name}", flush=True)
                await vc.move_to(channel)
            
            if not vc or not vc.is_connected():
                print(f"❌ VC not connected", flush=True)
                return False

            # Check FFmpeg
            ffmpeg_to_use = FFMPEG_EXE if (FFMPEG_EXE and os.path.exists(FFMPEG_EXE)) else shutil.which("ffmpeg")
            if not ffmpeg_to_use:
                print(f"❌ No FFmpeg found!", flush=True)
                return False

            print(f"🔊 Using FFmpeg: {ffmpeg_to_use}", flush=True)

            # Stop current if playing
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)

            tmp_file = None
            audio_file = None

            if beep_only:
                # Beep only - 100% works
                audio_file = BEEP_FILE
                print(f"🔔 Playing BEEP in {channel.name}", flush=True)
            else:
                # TTS
                if not text:
                    return False
                
                tmp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
                try:
                    print(f"🗣️ TTS generating: '{text}'", flush=True)
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(tmp_file)
                    print(f"✅ TTS saved {os.path.getsize(tmp_file)} bytes", flush=True)
                    audio_file = tmp_file
                except Exception as e:
                    print(f"❌ TTS fail: {e}, will play beep instead", flush=True)
                    audio_file = BEEP_FILE
                    tmp_file = None

            # Play
            try:
                source = discord.FFmpegPCMAudio(audio_file, executable=ffmpeg_to_use, options='-vn -loglevel quiet')
                print(f"▶️ PLAYING in {vc.channel.name}: {text or 'BEEP'}", flush=True)
                vc.play(source)

                # Wait max 10 sec
                start = time.time()
                while vc.is_playing() and (time.time() - start) < 10:
                    await asyncio.sleep(0.3)

                if vc.is_playing():
                    vc.stop()

                print(f"✅ PLAYED: {text or 'BEEP'}", flush=True)
                return True

            except Exception as e:
                print(f"❌ Play fail: {e}", flush=True)
                import traceback
                traceback.print_exc()
                return False
            finally:
                if tmp_file and os.path.exists(tmp_file):
                    try:
                        os.remove(tmp_file)
                    except:
                        pass

        except Exception as e:
            print(f"❌ play_audio error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 FINAL TTS BOT ONLINE! {bot.user}\nFFmpeg: {FFMPEG_EXE}\nGuilds: {len(bot.guilds)}\nNO AUTO-DISCONNECT - Will stay in VC forever!\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!join | Final Fix"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            # JOIN - Bot will join and speak, and STAY FOREVER
            text = f"{member.display_name} joined"
            text_bn = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text_bn} in {after.channel.name} - Bot will STAY, not leave", flush=True)
            await asyncio.sleep(0.5)
            await play_audio(member.guild, after.channel, text_bn, beep_only=False)

            # Text fallback
            if TEXT_CHANNEL_ID:
                try:
                    ch = bot.get_channel(TEXT_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(TEXT_CHANNEL_ID)
                    embed = discord.Embed(title="🎙️ Joined", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
                    await ch.send(embed=embed)
                except Exception as e:
                    print(f"Text fallback fail: {e}", flush=True)

        elif before.channel is not None and after.channel is None:
            text_bn = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text_bn} - Bot will STAY in VC, not leave", flush=True)
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await play_audio(member.guild, before.channel, text_bn, beep_only=False)
                # NO AUTO LEAVE - Stay forever!
                print(f"   -> Bot STAYING in {before.channel.name} (no auto-disconnect)", flush=True)

            if TEXT_CHANNEL_ID:
                try:
                    ch = bot.get_channel(TEXT_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(TEXT_CHANNEL_ID)
                    embed = discord.Embed(title="👋 Left", description=f"**{member.display_name}** left **{before.channel.name}**", color=discord.Color.red())
                    await ch.send(embed=embed)
                except:
                    pass

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text_bn = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text_bn}", flush=True)
            await asyncio.sleep(0.5)
            await play_audio(member.guild, after.channel, text_bn, beep_only=False)

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
                await ctx.send(f"✅ Already in {ch.mention} | Will STAY forever until !leave")
                return
            await vc.move_to(ch)
            await ctx.send(f"✅ Moved to {ch.mention} | Will STAY forever")
        else:
            await ch.connect()
            await ctx.send(f"✅ Joined {ch.mention}\n✅ Will STAY forever (no auto-disconnect)\nEkhon `!beep` then `!testvoice` koro")
    except Exception as e:
        await ctx.send(f"❌ Join fail: {e}")
        print(f"❌ Join fail: {e}", flush=True)

@bot.command(name="beep")
async def beep_cmd(ctx):
    """Beep test - 100% works, no internet needed"""
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age !join")
            return
    
    await ctx.send("🔔 Beep bajacchi... (100% works, no TTS)")
    success = await play_audio(ctx.guild, ctx.voice_client.channel, beep_only=True)
    if success:
        await ctx.send("✅ **Beep bajse!** Voice 100% kaj kore! Ekhon `!testvoice` koro TTS er jonno")
    else:
        await ctx.send(f"❌ Beep o fail! FFmpeg: {FFMPEG_EXE}")

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age VC te join koro, tarpor !join")
            return
    
    await ctx.send(f"🎙️ TTS test: '{ctx.author.display_name} voice e join korse'")
    success = await play_audio(ctx.guild, ctx.voice_client.channel, f"{ctx.author.display_name} voice e join korse", beep_only=False)
    if success:
        await ctx.send("✅ **TTS bajse!** Ekhon auto join/leave te bolbe + 5 min thakbe na, forever thakbe!")
    else:
        await ctx.send("❌ TTS fail, kintu `!beep` kaj korle `!say` diye try koro")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ Bolchi: {text}")
    await play_audio(ctx.guild, ctx.voice_client.channel, text, beep_only=False)

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left VC (manual !leave)")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="debug")
async def debug_cmd(ctx):
    vc = ctx.voice_client
    await ctx.send(f"""
**FINAL DEBUG - No Auto Disconnect**
Bot VC: {vc.channel.name if vc else 'None'} | Connected: {vc.is_connected() if vc else False}
FFmpeg: {FFMPEG_EXE or 'NOT FOUND'} | Exists: {os.path.exists(FFMPEG_EXE) if FFMPEG_EXE else False}
Beep: {os.path.exists(BEEP_FILE)} | {os.path.getsize(BEEP_FILE) if os.path.exists(BEEP_FILE) else 0} bytes
Opus: {discord.opus.is_loaded()}
Stay: FOREVER until !leave (no auto-disconnect)
""")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(FFMPEG_EXE)} | VC: {bool(ctx.voice_client)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting FINAL TTS Bot - NO AUTO-DISCONNECT, Beep+TTS...", flush=True)
    bot.run(TOKEN)
