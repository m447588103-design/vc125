"""
🐺 WHITE_WOLF Voice TTS Bot - MULTI-SERVER SUPPORT
2 server er jonno 2 ta alada notification channel ID env te deya jabe!
+ Render host fix (no apt-get, imageio-ffmpeg)
"""

import os
import asyncio
import threading
import time
import uuid
import shutil
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands
from gtts import gTTS

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# ========== MULTI-SERVER CHANNEL ID SUPPORT ==========
# 3 ta way te dite parba:

# Way 1 (Recommended for 2 servers): JSON format
# NOTIFICATION_CHANNELS = {"123456789012345678": 987654321098765432, "234567890123456789": 876543210987654321}
# Key = Server (Guild) ID, Value = Text Channel ID

# Way 2: guild:channel,guild:channel format
# NOTIFICATION_CHANNELS = 123456789012345678:987654321098765432,234567890123456789:876543210987654321

# Way 3 (Single server): Single ID (old way, still works)
# NOTIFICATION_CHANNEL_ID = 987654321098765432

def load_channel_map():
    """Load multi-server channel mapping from env"""
    # Try NOTIFICATION_CHANNELS first (new), then NOTIFICATION_CHANNEL_ID (old)
    raw = os.getenv('NOTIFICATION_CHANNELS') or os.getenv('NOTIFICATION_CHANNEL_ID') or ""
    raw = raw.strip()
    
    if not raw:
        print("❌ No channel ID env found! Set NOTIFICATION_CHANNELS or NOTIFICATION_CHANNEL_ID", flush=True)
        return {}, None

    print(f"🔧 Raw channel env: {raw[:100]}...", flush=True)

    # Way 1: JSON {"guild_id": channel_id, ...}
    if raw.startswith('{'):
        try:
            data = json.loads(raw)
            mapping = {int(k): int(v) for k, v in data.items()}
            print(f"✅ Loaded JSON mapping for {len(mapping)} servers: {mapping}", flush=True)
            return mapping, None
        except Exception as e:
            print(f"❌ JSON parse fail: {e}", flush=True)

    # Way 2: guild:channel,guild:channel
    if ':' in raw and ',' in raw:
        try:
            mapping = {}
            pairs = raw.split(',')
            for pair in pairs:
                pair = pair.strip()
                if ':' in pair:
                    gid, cid = pair.split(':', 1)
                    mapping[int(gid.strip())] = int(cid.strip())
            if mapping:
                print(f"✅ Loaded guild:channel mapping for {len(mapping)} servers: {mapping}", flush=True)
                return mapping, None
        except Exception as e:
            print(f"❌ guild:channel parse fail: {e}", flush=True)

    # Way 2b: Single guild:channel (for 1 server but explicit)
    if ':' in raw and ',' not in raw:
        try:
            gid, cid = raw.split(':', 1)
            mapping = {int(gid.strip()): int(cid.strip())}
            print(f"✅ Loaded single guild:channel mapping: {mapping}", flush=True)
            return mapping, None
        except Exception as e:
            print(f"❌ single guild:channel parse fail: {e}", flush=True)

    # Way 3: Single channel ID for all servers (old way)
    try:
        # Remove any non-digit except for first char?
        # Try to parse as int
        single_id = int(raw)
        print(f"✅ Single channel ID for all servers: {single_id}", flush=True)
        return {}, single_id
    except:
        pass

    # Way 4: Comma-separated channel IDs (broadcast to all)
    if ',' in raw:
        try:
            ids = [int(x.strip()) for x in raw.split(',') if x.strip().isdigit() or x.strip().lstrip('-').isdigit()]
            # Actually try int conversion
            ids = []
            for x in raw.split(','):
                x = x.strip()
                try:
                    ids.append(int(x))
                except:
                    pass
            if ids:
                print(f"✅ Multiple channel IDs (broadcast): {ids}", flush=True)
                # Return as list in single_id? We'll handle as list
                return {}, ids
        except Exception as e:
            print(f"❌ Comma list parse fail: {e}", flush=True)

    print(f"❌ Could not parse channel env: {raw}", flush=True)
    return {}, None

CHANNEL_MAP, SINGLE_CHANNEL_ID = load_channel_map()
# SINGLE_CHANNEL_ID can be int or list

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | MAP={CHANNEL_MAP} | SINGLE={SINGLE_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# ========== FFMPEG SETUP (No apt-get) ==========
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg via imageio-ffmpeg: {FFMPEG_EXE}", flush=True)
except Exception as e:
    print(f"⚠️ imageio-ffmpeg not found: {e}", flush=True)
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"   System FFmpeg: {FFMPEG_EXE}", flush=True)

if not FFMPEG_EXE:
    print("❌ FFmpeg NOT FOUND!", flush=True)
else:
    print(f"✅ Using FFmpeg: {FFMPEG_EXE}", flush=True)

# Opus
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

# ========== WEB SERVER ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Multi-Server TTS Bot')
        else:
            self.wfile.write(f"Multi-Server Bot | Guilds: {len(CHANNEL_MAP) if CHANNEL_MAP else 'single'} | FFmpeg: {bool(FFMPEG_EXE)}".encode())
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Web on 0.0.0.0:{PORT}...", flush=True)
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

def get_notification_channels(guild):
    """Get notification channel(s) for a guild - multi-server support"""
    channels = []
    
    # Way 1 & 2: Mapping has guild ID
    if guild.id in CHANNEL_MAP:
        cid = CHANNEL_MAP[guild.id]
        ch = guild.get_channel(cid) or bot.get_channel(cid)
        if ch:
            channels.append(ch)
        else:
            # Try fetch
            print(f"⚠️ Channel {cid} not in cache for guild {guild.name}, will try fetch later", flush=True)
            # Return ID for fetch later
            channels.append(cid)  # ID, will fetch in async context
        return channels
    
    # Way 3: Single ID for all servers
    if SINGLE_CHANNEL_ID:
        if isinstance(SINGLE_CHANNEL_ID, list):
            # Broadcast to multiple channels
            for cid in SINGLE_CHANNEL_ID:
                ch = guild.get_channel(cid) or bot.get_channel(cid)
                if ch:
                    channels.append(ch)
                else:
                    # Check if channel belongs to this guild? For broadcast, we try to find in this guild
                    # If not found, skip
                    pass
            return channels
        elif isinstance(SINGLE_CHANNEL_ID, int):
            ch = guild.get_channel(SINGLE_CHANNEL_ID) or bot.get_channel(SINGLE_CHANNEL_ID)
            if ch:
                channels.append(ch)
            else:
                # For single ID, try to fetch - might be in this guild
                channels.append(SINGLE_CHANNEL_ID)
            return channels
    
    # No mapping found
    print(f"❌ No notification channel configured for guild {guild.name} ({guild.id})", flush=True)
    return []

async def get_notification_channels_async(guild):
    """Async version that fetches if needed"""
    channels = []
    raw_channels = get_notification_channels(guild)
    
    for item in raw_channels:
        if isinstance(item, int):
            # It's an ID, need to fetch
            try:
                ch = guild.get_channel(item)
                if not ch:
                    ch = bot.get_channel(item)
                if not ch:
                    ch = await bot.fetch_channel(item)
                if ch:
                    channels.append(ch)
            except Exception as e:
                print(f"❌ Failed to fetch channel {item} for guild {guild.name}: {e}", flush=True)
        else:
            # Already channel object
            channels.append(item)
    
    return channels

async def send_notification(guild, embed=None, content=None):
    """Send to all notification channels for this guild"""
    channels = await get_notification_channels_async(guild)
    if not channels:
        print(f"❌ No channels to send notification for guild {guild.name}", flush=True)
        return
    
    for ch in channels:
        try:
            if embed:
                await ch.send(embed=embed)
            elif content:
                await ch.send(content)
            print(f"✅ Notification sent to #{ch.name} in {guild.name}", flush=True)
        except Exception as e:
            print(f"❌ Failed to send to #{ch.name}: {e}", flush=True)

async def tts_speak(guild, channel, text):
    """TTS speak in VC"""
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
            print(f"🗣️ TTS: '{text}'", flush=True)
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(tmp_file)
            
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)
            
            print(f"▶️ Playing in {channel.name}: {text}", flush=True)
            
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
    print(f"\n{'='*60}\n🐺 MULTI-SERVER TTS BOT ONLINE! {bot.user}\nGuilds: {len(bot.guilds)} | Channel Map: {CHANNEL_MAP} | Single: {SINGLE_CHANNEL_ID}\n{'='*60}\n", flush=True)
    for guild in bot.guilds:
        print(f" - {guild.name} ({guild.id})", flush=True)
        channels = await get_notification_channels_async(guild)
        if channels:
            for ch in channels:
                print(f"   ✅ Notification: #{ch.name} ({ch.id})", flush=True)
        else:
            print(f"   ❌ No notification channel configured for this guild!", flush=True)
            print(f"      Set NOTIFICATION_CHANNELS env with {guild.id}:<channel_id>", flush=True)
    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Multi-Server | !help"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | Guild: {member.guild.name} ({member.guild.id})", flush=True)

    try:
        if before.channel is None and after.channel is not None:
            text = f"{member.display_name} voice e join korse"
            print(f"   -> JOIN: {text}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text)
            
            # Text notification to correct server's channel
            embed = discord.Embed(title="🎙️ Voice Joined", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Channel", value=after.channel.mention, inline=True)
            await send_notification(member.guild, embed=embed)

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
            
            embed = discord.Embed(title="👋 Voice Left", description=f"**{member.display_name}** left **{before.channel.name}**", color=discord.Color.red())
            await send_notification(member.guild, embed=embed)

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text)
            
            embed = discord.Embed(title="🔄 Voice Moved", description=f"**{member.display_name}** moved {before.channel.name} -> {after.channel.name}", color=discord.Color.blue())
            await send_notification(member.guild, embed=embed)

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
            await ctx.send(f"✅ Joined {ch.mention} | Ekhon kew join korle bolbo!")
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

@bot.command(name="testtext")
async def testtext_cmd(ctx):
    embed = discord.Embed(title="✅ Test", description=f"Test by {ctx.author.mention} | Guild: {ctx.guild.name} ({ctx.guild.id})", color=discord.Color.green())
    await send_notification(ctx.guild, embed=embed)
    await ctx.send(f"✅ Test sent to notification channel(s) for this server!")

@bot.command(name="debug")
async def debug_cmd(ctx):
    channels = await get_notification_channels_async(ctx.guild)
    ch_list = ", ".join([f"#{c.name} ({c.id})" for c in channels]) if channels else "NOT CONFIGURED ❌"
    
    await ctx.send(f"""
**🔍 MULTI-SERVER DEBUG**
**This Guild:** {ctx.guild.name} ({ctx.guild.id})
**This Guild's Notification Channel(s):** {ch_list}
**All Mappings:** `{CHANNEL_MAP}`
**Single ID:** `{SINGLE_CHANNEL_ID}`
**Your VC:** {ctx.author.voice.channel.name if ctx.author.voice else 'Not in VC'}
**Bot VC:** {ctx.voice_client.channel.name if ctx.voice_client else 'Not in VC'}
**FFmpeg:** {FFMPEG_EXE or 'NOT FOUND'}
**Opus:** {discord.opus.is_loaded()}

**How to set 2 servers:**
Env `NOTIFICATION_CHANNELS` e:
`{{"{ctx.guild.id}": 123456789012345678}}`
Ba 2 server er jonno:
`{{"111111111111111111": 222222222222222222, "333333333333333333": 444444444444444444}}`
Ba: `111111111111111111:222222222222222222,333333333333333333:444444444444444444`
""")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(FFMPEG_EXE)} | Guild: {ctx.guild.name}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 Multi-Server TTS Bot", description="2 server er jonno alada channel ID", color=discord.Color.green())
    embed.add_field(name="🎙️ Auto", value="Join/Leave/Move voice e bolbe + text e notification", inline=False)
    embed.add_field(name="Commands", value="`!join` `!leave` `!say <text>` `!testvoice` `!testtext` `!debug`", inline=False)
    embed.add_field(name="Multi-Server Setup", value="Env `NOTIFICATION_CHANNELS` e JSON:\n`{\"guild_id\": channel_id, \"guild_id2\": channel_id2}`\nBa `guild:channel,guild:channel`", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting Multi-Server TTS Bot...", flush=True)
    bot.run(TOKEN)
