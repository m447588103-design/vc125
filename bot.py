"""
FINAL ATTEMPT - Keepalive + Auto-Reconnect Loop
Bot VC te thakbe na mane Render UDP disconnect kore
Keepalive task diye reconnect korbe + Railway alternative
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
TEXT_CH_ID = os.getenv('NOTIFICATION_CHANNELS') or os.getenv('NOTIFICATION_CHANNEL_ID')
try:
    if TEXT_CH_ID and '{' in TEXT_CH_ID:
        import json
        TEXT_CH_ID = list(json.loads(TEXT_CH_ID).values())[0]
    elif TEXT_CH_ID and ':' in TEXT_CH_ID:
        TEXT_CH_ID = int(TEXT_CH_ID.split(':')[1].split(',')[0].strip())
    elif TEXT_CH_ID:
        TEXT_CH_ID = int(str(TEXT_CH_ID).split(',')[0].strip())
    else:
        TEXT_CH_ID = None
except:
    TEXT_CH_ID = None

print(f"🔧 TOKEN={bool(TOKEN)} PORT={PORT} TEXT_CH={TEXT_CH_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# FFmpeg
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg: {FFMPEG_EXE}", flush=True)
except:
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"FFmpeg: {FFMPEG_EXE}", flush=True)

# Beep file
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
        print(f"✅ Beep {os.path.getsize(BEEP_FILE)} bytes", flush=True)
        return True
    except Exception as e:
        print(f"❌ Beep fail: {e}", flush=True)
        return False

make_beep()

# Web server
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Keepalive Voice Bot')
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

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Track where bot should stay
should_stay = {}  # guild_id -> channel
voice_locks = {}

async def keepalive_loop():
    """Background task - every 10 sec check if bot should be in VC but disconnected, then reconnect"""
    await bot.wait_until_ready()
    print("🔄 Keepalive loop started - will auto-reconnect if VC disconnects", flush=True)
    while not bot.is_closed():
        try:
            for guild_id, channel in list(should_stay.items()):
                guild = bot.get_guild(guild_id)
                if not guild:
                    continue
                
                vc = guild.voice_client
                if vc is None or not vc.is_connected():
                    print(f"⚠️ Keepalive: Bot should be in {channel.name} but disconnected! Reconnecting...", flush=True)
                    try:
                        # Try to reconnect
                        if vc:
                            try:
                                await vc.disconnect(force=True)
                            except:
                                pass
                        new_vc = await channel.connect(timeout=15, self_deaf=False)
                        print(f"✅ Keepalive reconnected to {channel.name}", flush=True)
                        # Play beep to confirm
                        try:
                            if os.path.exists(BEEP_FILE) and FFMPEG_EXE:
                                source = discord.FFmpegPCMAudio(BEEP_FILE, executable=FFMPEG_EXE, options='-vn -loglevel quiet')
                                new_vc.play(source)
                        except:
                            pass
                    except Exception as e:
                        print(f"❌ Keepalive reconnect fail for {channel.name}: {e}", flush=True)
                else:
                    # Still connected, log every 60 sec
                    pass
            
            await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Keepalive loop error: {e}", flush=True)
            await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 KEEPALIVE VOICE BOT ONLINE! {bot.user}\nFFmpeg: {FFMPEG_EXE} | Opus: {discord.opus.is_loaded()}\n{'='*60}\n", flush=True)
    # Start keepalive task
    bot.loop.create_task(keepalive_loop())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!join = stay forever"))

async def play_audio(guild, channel, text=None, beep_only=False):
    """Play audio with keepalive"""
    gid = guild.id
    if gid not in voice_locks:
        voice_locks[gid] = asyncio.Lock()
    
    async with voice_locks[gid]:
        try:
            vc = guild.voice_client
            if vc is None:
                print(f"🔊 JOINING {channel.name} for {text or 'beep'}", flush=True)
                vc = await channel.connect(timeout=15, self_deaf=False)
                print(f"✅ JOINED {channel.name}", flush=True)
                should_stay[guild.id] = channel  # Mark to stay
            elif vc.channel.id != channel.id:
                print(f"🔄 MOVING to {channel.name}", flush=True)
                await vc.move_to(channel)
                should_stay[guild.id] = channel
            
            if not vc or not vc.is_connected():
                print(f"❌ VC not connected", flush=True)
                return False

            ffmpeg_to_use = FFMPEG_EXE if (FFMPEG_EXE and os.path.exists(FFMPEG_EXE)) else shutil.which("ffmpeg")
            if not ffmpeg_to_use:
                print(f"❌ No FFmpeg", flush=True)
                return False

            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)

            tmp_file = None
            audio_file = None

            if beep_only:
                audio_file = BEEP_FILE
                print(f"🔔 BEEP in {channel.name}", flush=True)
            else:
                if not text:
                    return False
                tmp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
                try:
                    print(f"🗣️ TTS: '{text}'", flush=True)
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(tmp_file)
                    print(f"✅ TTS {os.path.getsize(tmp_file)} bytes", flush=True)
                    audio_file = tmp_file
                except Exception as e:
                    print(f"❌ TTS fail: {e}, beep fallback", flush=True)
                    audio_file = BEEP_FILE
                    tmp_file = None

            try:
                source = discord.FFmpegPCMAudio(audio_file, executable=ffmpeg_to_use, options='-vn -loglevel quiet')
                print(f"▶️ PLAYING in {vc.channel.name}: {text or 'BEEP'}", flush=True)
                vc.play(source)

                start = time.time()
                while vc.is_playing() and (time.time() - start) < 10:
                    await asyncio.sleep(0.3)

                if vc.is_playing():
                    vc.stop()

                print(f"✅ PLAYED", flush=True)
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
async def on_voice_state_update(member, before, after):
    if member.bot:
        if member.id == bot.user.id:
            if before.channel is None and after.channel is not None:
                print(f"🤖 BOT JOINED {after.channel.name}", flush=True)
                should_stay[member.guild.id] = after.channel
            elif before.channel is not None and after.channel is None:
                print(f"🤖 BOT LEFT {before.channel.name} | should_stay={member.guild.id in should_stay}", flush=True)
                # If should stay but left, keepalive will reconnect
                if member.guild.id in should_stay:
                    print(f"   -> Bot should stay in {before.channel.name}, keepalive will reconnect in 10s", flush=True)
                else:
                    print(f"   -> Bot left intentionally (!leave)", flush=True)
            return
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            text = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text} in {after.channel.name}", flush=True)
            await asyncio.sleep(0.5)
            await play_audio(member.guild, after.channel, text, beep_only=False)
            
            if TEXT_CH_ID:
                try:
                    ch = bot.get_channel(TEXT_CH_ID) or await bot.fetch_channel(TEXT_CH_ID)
                    embed = discord.Embed(title="🎙️ Joined", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
                    await ch.send(embed=embed)
                except:
                    pass

        elif before.channel is not None and after.channel is None:
            text = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text}", flush=True)
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await play_audio(member.guild, before.channel, text, beep_only=False)
                print(f"   -> Bot STAYING in {before.channel.name} (keepalive will keep it)", flush=True)
                # NO AUTO LEAVE - keepalive keeps it

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
                await ctx.send(f"✅ Already in {ch.mention} | Staying forever until !leave | Keepalive ON")
                should_stay[ctx.guild.id] = ch
                return
            await vc.move_to(ch)
            should_stay[ctx.guild.id] = ch
            await ctx.send(f"✅ Moved to {ch.mention} | Keepalive ON - Will auto-reconnect if disconnects")
        else:
            await ch.connect()
            should_stay[ctx.guild.id] = ch
            await ctx.send(f"✅ Joined {ch.mention}\n✅ Keepalive ON - Bot will stay forever & auto-reconnect if Render disconnects!\nEkhon `!beep` then `!testvoice`")
    except Exception as e:
        await ctx.send(f"❌ Join fail: {e}")
        print(f"❌ Join fail: {e}", flush=True)

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        should_stay.pop(ctx.guild.id, None)
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left VC (keepalive OFF)")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="beep")
async def beep_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
                should_stay[ctx.guild.id] = ctx.author.voice.channel
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age !join")
            return
    
    await ctx.send("🔔 Beep bajacchi... (100% works)")
    success = await play_audio(ctx.guild, ctx.voice_client.channel, beep_only=True)
    if success:
        await ctx.send("✅ **Beep bajse!** Voice works! Keepalive ON - Bot will stay")
    else:
        await ctx.send(f"❌ Beep fail! FFmpeg: {FFMPEG_EXE}")

@bot.command(name="testvoice")
async def testvoice_cmd(ctx):
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
                should_stay[ctx.guild.id] = ctx.author.voice.channel
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age VC te join koro, tarpor !join")
            return
    
    await ctx.send(f"🎙️ TTS: '{ctx.author.display_name} voice e join korse'")
    success = await play_audio(ctx.guild, ctx.voice_client.channel, f"{ctx.author.display_name} voice e join korse", beep_only=False)
    if success:
        await ctx.send("✅ **TTS bajse!** Ekhon auto join/leave bolbe + forever thakbe!")
    else:
        await ctx.send("❌ TTS fail, `!beep` try koro")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect()
                should_stay[ctx.guild.id] = ctx.author.voice.channel
            except Exception as e:
                await ctx.send(f"❌ Join fail: {e}")
                return
        else:
            await ctx.send("❌ Age !join")
            return
    await ctx.send(f"🗣️ Bolchi: {text}")
    await play_audio(ctx.guild, ctx.voice_client.channel, text, beep_only=False)

@bot.command(name="debug")
async def debug_cmd(ctx):
    vc = ctx.voice_client
    await ctx.send(f"""
**FINAL DEBUG - Keepalive**
Bot VC: {vc.channel.name if vc else 'None'} | Connected: {vc.is_connected() if vc else False}
Should Stay: {ctx.guild.id in should_stay} -> {should_stay.get(ctx.guild.id).name if ctx.guild.id in should_stay else 'No'}
FFmpeg: {FFMPEG_EXE or 'NOT FOUND'}
Opus: {discord.opus.is_loaded()}
Keepalive: Every 10s auto-reconnect if disconnects
Stay: FOREVER until !leave
""")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(FFMPEG_EXE)} | Keepalive: ON")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting FINAL Keepalive Voice Bot - Stay Forever + Auto-Reconnect...", flush=True)
    bot.run(TOKEN)
