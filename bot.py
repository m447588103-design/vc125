"""
DEBUG VERSION - Voice connection test without TTS
To check if Render supports voice at all
"""

import os
import threading
import time
import shutil
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNEL_ID')  # Optional fallback text channel
if NOTIFICATION_CHANNEL_ID:
    try:
        NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID)
    except:
        NOTIFICATION_CHANNEL_ID = None
else:
    NOTIFICATION_CHANNEL_ID = None

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | TEXT_CHANNEL={NOTIFICATION_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# Check FFmpeg and Opus
print("🔍 Checking FFmpeg & Opus...", flush=True)
ffmpeg_path = shutil.which("ffmpeg")
print(f"FFmpeg path: {ffmpeg_path}", flush=True)
if ffmpeg_path:
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        print(f"✅ FFmpeg: {r.stdout.splitlines()[0]}", flush=True)
    except Exception as e:
        print(f"⚠️ FFmpeg check fail: {e}", flush=True)
else:
    print("❌ FFmpeg NOT FOUND!", flush=True)

try:
    import nacl
    print(f"✅ PyNaCl installed: {nacl.__version__}", flush=True)
except Exception as e:
    print(f"❌ PyNaCl missing: {e}", flush=True)

# Check opus
try:
    if discord.opus.is_loaded():
        print("✅ Opus already loaded", flush=True)
    else:
        # Try to load
        try:
            discord.opus.load_opus('libopus.so.0')
            print("✅ Opus loaded via libopus.so.0", flush=True)
        except:
            try:
                discord.opus.load_opus('libopus.so')
                print("✅ Opus loaded via libopus.so", flush=True)
            except Exception as e:
                print(f"⚠️ Opus not loaded, will try auto: {e}", flush=True)
                # Try auto
                if not discord.opus.is_loaded():
                    print("❌ Opus NOT loaded - voice may fail!", flush=True)
                else:
                    print("✅ Opus auto-loaded", flush=True)
except Exception as e:
    print(f"⚠️ Opus check error: {e}", flush=True)

# Web server
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Debug Voice Bot')
        else:
            self.wfile.write(f"Debug Voice Bot | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}".encode())
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

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 DEBUG VOICE BOT ONLINE! {bot.user}\nFFmpeg: {ffmpeg_path} | Opus loaded: {discord.opus.is_loaded()}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Debug Mode | !join"))

@bot.event
async def on_voice_state_update(member, before, after):
    # Log ALL voice events including bot's own
    print(f"[VOICE] {member.display_name} (bot={member.bot}) | {before.channel} -> {after.channel} | Guild: {member.guild.name}", flush=True)
    
    if member.id == bot.user.id:
        # Bot's own voice state changed
        if before.channel is None and after.channel is not None:
            print(f"   🤖 BOT JOINED {after.channel.name}", flush=True)
        elif before.channel is not None and after.channel is None:
            print(f"   🤖 BOT LEFT/DISCONNECTED from {before.channel.name} | Reason: {after}", flush=True)
            # Log why disconnected
            if after.channel is None:
                print(f"   ⚠️ Bot was disconnected! Check if Render blocks UDP or voice", flush=True)
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            print(f"   🤖 BOT MOVED {before.channel.name} -> {after.channel.name}", flush=True)
        return

    if member.bot:
        return

    # For normal users - just log, and if bot in VC, try to announce via TEXT as fallback
    if before.channel is None and after.channel is not None:
        print(f"   -> USER JOIN: {member.display_name} -> {after.channel.name}", flush=True)
        # Fallback text notification if voice fails
        if NOTIFICATION_CHANNEL_ID:
            try:
                ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                if not ch:
                    ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                if ch:
                    await ch.send(f"🎙️ **{member.display_name}** joined **{after.channel.name}** (Voice debug mode - text fallback)")
            except Exception as e:
                print(f"   -> Text fallback fail: {e}", flush=True)

    elif before.channel is not None and after.channel is None:
        print(f"   -> USER LEAVE: {member.display_name} <- {before.channel.name}", flush=True)
        if NOTIFICATION_CHANNEL_ID:
            try:
                ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                if not ch:
                    ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                if ch:
                    await ch.send(f"👋 **{member.display_name}** left **{before.channel.name}**")
            except:
                pass

@bot.command(name="join")
async def join_cmd(ctx):
    """Debug join - just join, no TTS"""
    if not ctx.author.voice:
        await ctx.send("❌ Age VC te join koro!")
        return
    
    ch = ctx.author.voice.channel
    print(f"🔊 !join requested -> {ch.name} by {ctx.author}", flush=True)
    
    try:
        vc = ctx.voice_client
        if vc:
            if vc.channel.id == ch.id:
                await ctx.send(f"✅ Already in {ch.mention} | Connected: {vc.is_connected()} | Opus: {discord.opus.is_loaded()} | FFmpeg: {bool(ffmpeg_path)}")
                return
            else:
                print(f"🔄 Moving to {ch.name}", flush=True)
                await vc.move_to(ch)
                await ctx.send(f"✅ Moved to {ch.mention}")
                return
        else:
            print(f"🔊 Connecting to {ch.name}...", flush=True)
            vc = await ch.connect(timeout=15, self_deaf=False, self_mute=False, self_stream=False)
            print(f"✅ Connected to {ch.name} | VC: {vc} | Connected: {vc.is_connected()}", flush=True)
            await ctx.send(f"✅ Joined {ch.mention}\nConnected: {vc.is_connected()}\nOpus: {discord.opus.is_loaded()}\nFFmpeg: {ffmpeg_path}\n\nEkhon 60 sec wait koro, disconnect hoy kina dekho. Jodi disconnect na hoy, tahole voice support kore. Jodi disconnect hoy, Render voice block kore.")
            
            # Monitor connection for 60s
            for i in range(12):
                await asyncio.sleep(5)
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    print(f"❌ VC disconnected after {i*5}s!", flush=True)
                    await ctx.send(f"❌ Bot disconnected after {i*5} seconds! Render may block voice UDP.")
                    return
                print(f"   -> Still connected after {i*5}s | Channel: {ctx.voice_client.channel.name}", flush=True)
            
            await ctx.send("✅ Bot stayed 60s without disconnect! Voice works on Render, TTS issue chilo. Ebar TTS version e jabo.")
            
    except Exception as e:
        print(f"❌ Join failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        await ctx.send(f"❌ Join failed: {e}\nFFmpeg: {ffmpeg_path}\nOpus: {discord.opus.is_loaded()}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left")
    else:
        await ctx.send("❌ Not in VC")

@bot.command(name="debugvoice")
async def debugvoice_cmd(ctx):
    vc = ctx.voice_client
    embed = discord.Embed(title="🔍 Voice Debug", color=discord.Color.blue())
    embed.add_field(name="FFmpeg", value=f"{ffmpeg_path or 'NOT FOUND'}", inline=False)
    embed.add_field(name="Opus Loaded", value=f"{discord.opus.is_loaded()}", inline=True)
    embed.add_field(name="PyNaCl", value="Installed" if 'nacl' in globals() else "Check logs", inline=True)
    embed.add_field(name="Voice Client", value=f"{vc.channel.name if vc else 'None'} | Connected: {vc.is_connected() if vc else False}", inline=False)
    embed.add_field(name="User VC", value=f"{ctx.author.voice.channel.name if ctx.author.voice else 'Not in VC'}", inline=False)
    embed.add_field(name="Render Voice", value="Render Free Web Service may block UDP. If bot disconnects instantly, use Railway.app or VPS", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="testtts")
async def testtts_cmd(ctx):
    """Test gTTS without playing in VC - just generate file"""
    await ctx.send("🔍 Testing gTTS generation...")
    try:
        from gtts import gTTS
        import uuid, os
        filename = f"/tmp/test_{uuid.uuid4().hex}.mp3"
        tts = gTTS(text="Hello, this is a test", lang='en', slow=False)
        tts.save(filename)
        size = os.path.getsize(filename)
        await ctx.send(f"✅ gTTS OK! File: {filename} Size: {size} bytes | FFmpeg: {ffmpeg_path}")
        os.remove(filename)
    except Exception as e:
        await ctx.send(f"❌ gTTS failed: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting DEBUG Voice Bot...", flush=True)
    bot.run(TOKEN)
