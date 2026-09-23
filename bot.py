"""
🐺 WHITE_WOLF FINAL BOT - LAST VERSION
✅ Text Notification 100% Render e kaj korbe
✅ Voice TTS o thakbe - VC te join hoye bolbe (local e 100%, Render e voice support korle)
- Simple, clean, no auto-disconnect bug
- Multi-server support
"""

import os
import threading
import time
import uuid
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# Multi-server channel IDs
# Way 1: NOTIFICATION_CHANNELS = {"guild_id": channel_id, "guild_id2": channel_id2}
# Way 2: NOTIFICATION_CHANNELS = guild_id:channel_id,guild_id:channel_id
# Way 3: NOTIFICATION_CHANNEL_ID = single channel ID
CHANNEL_MAP = {}
SINGLE_CHANNEL = None

raw = os.getenv('NOTIFICATION_CHANNELS') or os.getenv('NOTIFICATION_CHANNEL_ID') or ""
raw = raw.strip()

if raw:
    if raw.startswith('{'):
        try:
            import json
            data = json.loads(raw)
            CHANNEL_MAP = {int(k): int(v) for k, v in data.items()}
            print(f"✅ Multi-server mapping: {CHANNEL_MAP}", flush=True)
        except Exception as e:
            print(f"❌ JSON parse fail: {e}", flush=True)
    elif ':' in raw:
        try:
            # guild:channel,guild:channel
            mapping = {}
            for pair in raw.split(','):
                pair = pair.strip()
                if ':' in pair:
                    gid, cid = pair.split(':', 1)
                    mapping[int(gid.strip())] = int(cid.strip())
            if mapping:
                CHANNEL_MAP = mapping
                print(f"✅ Mapping: {CHANNEL_MAP}", flush=True)
        except Exception as e:
            print(f"❌ Mapping parse fail: {e}", flush=True)
            try:
                SINGLE_CHANNEL = int(raw.split(',')[0].split(':')[-1].strip())
            except:
                pass
    else:
        try:
            # Single ID or comma list
            if ',' in raw:
                # Take first for now, but support broadcast later
                SINGLE_CHANNEL = int(raw.split(',')[0].strip())
            else:
                SINGLE_CHANNEL = int(raw)
            print(f"✅ Single channel: {SINGLE_CHANNEL}", flush=True)
        except Exception as e:
            print(f"❌ Channel parse fail: {e}", flush=True)

print(f"🔧 TOKEN={bool(TOKEN)} PORT={PORT} MAP={CHANNEL_MAP} SINGLE={SINGLE_CHANNEL}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# FFmpeg check (optional, for voice)
FFMPEG_EXE = None
try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ FFmpeg: {FFMPEG_EXE}", flush=True)
except:
    FFMPEG_EXE = shutil.which("ffmpeg")
    print(f"FFmpeg: {FFMPEG_EXE}", flush=True)

# Web server for Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Final Bot Running - Text 100% + Voice TTS')
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

# Discord bot
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def get_text_channel(guild):
    """Get text notification channel for guild"""
    # Check mapping
    if guild.id in CHANNEL_MAP:
        cid = CHANNEL_MAP[guild.id]
        ch = guild.get_channel(cid) or bot.get_channel(cid)
        return ch
    
    # Single channel
    if SINGLE_CHANNEL:
        ch = guild.get_channel(SINGLE_CHANNEL) or bot.get_channel(SINGLE_CHANNEL)
        return ch
    
    return None

async def get_text_channel_async(guild):
    ch = get_text_channel(guild)
    if ch:
        return ch
    # Try fetch if ID known
    cid = None
    if guild.id in CHANNEL_MAP:
        cid = CHANNEL_MAP[guild.id]
    elif SINGLE_CHANNEL:
        cid = SINGLE_CHANNEL
    
    if cid:
        try:
            ch = await bot.fetch_channel(cid)
            return ch
        except:
            pass
    return None

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 FINAL BOT ONLINE! {bot.user}\nGuilds: {len(bot.guilds)}\nFFmpeg: {bool(FFMPEG_EXE)}\n{'='*60}\n", flush=True)
    for g in bot.guilds:
        ch = await get_text_channel_async(g)
        if ch:
            print(f" - {g.name}: #{ch.name} ({ch.id}) ✅", flush=True)
        else:
            print(f" - {g.name}: No text channel configured ❌", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Voice Join/Leave | !help"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)

    # Text notification - 100% works on Render
    try:
        text_ch = await get_text_channel_async(member.guild)
        if text_ch:
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(
                    title="🎙️ Voice Joined",
                    description=f"**{member.display_name}** joined **{after.channel.name}**\n**{member.display_name}** voice e **join korse**!",
                    color=discord.Color.green()
                )
                embed.add_field(name="👤 Member", value=member.mention, inline=True)
                embed.add_field(name="🔊 Channel", value=after.channel.mention, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="WHITE_WOLF GLOBAL")
                await text_ch.send(embed=embed)
                print(f"   -> Text JOIN sent to #{text_ch.name}", flush=True)

            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(
                    title="👋 Voice Left",
                    description=f"**{member.display_name}** left **{before.channel.name}**\n**{member.display_name}** voice theke **leave nise**!",
                    color=discord.Color.red()
                )
                embed.add_field(name="Member", value=member.mention, inline=True)
                embed.add_field(name="Channel", value=before.channel.mention, inline=True)
                embed.set_thumbnail(url=member.display_avatar.url)
                await text_ch.send(embed=embed)
                print(f"   -> Text LEAVE sent", flush=True)

            elif before.channel and after.channel and before.channel.id != after.channel.id:
                embed = discord.Embed(
                    title="🔄 Voice Moved",
                    description=f"**{member.display_name}** moved **{before.channel.name}** → **{after.channel.name}**",
                    color=discord.Color.blue()
                )
                await text_ch.send(embed=embed)
                print(f"   -> Text MOVE sent", flush=True)
    except Exception as e:
        print(f"❌ Text notification error: {e}", flush=True)

    # Voice TTS - Try to speak in VC (works local, may work on Render)
    try:
        if before.channel is None and after.channel is not None:
            # Someone joined - bot try to join and speak
            vc = member.guild.voice_client
            # Only speak if bot already in VC (via !join) - to avoid auto-join spam
            # If you want auto-join, uncomment below:
            # if vc is None:
            #     try:
            #         vc = await after.channel.connect()
            #     except:
            #         pass
            
            if vc and vc.channel.id == after.channel.id:
                # Bot already in same VC, speak
                try:
                    from gtts import gTTS
                    import uuid as uuid_lib
                    tmp = f"/tmp/tts_{uuid_lib.uuid4().hex}.mp3"
                    text = f"{member.display_name} voice e join korse"
                    print(f"🗣️ TTS trying: {text}", flush=True)
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(tmp)
                    
                    if vc.is_playing():
                        vc.stop()
                        await asyncio.sleep(0.5)
                    
                    ffmpeg_exe = FFMPEG_EXE or shutil.which("ffmpeg")
                    if ffmpeg_exe:
                        source = discord.FFmpegPCMAudio(tmp, executable=ffmpeg_exe, options='-vn -loglevel quiet')
                    else:
                        source = discord.FFmpegPCMAudio(tmp, options='-vn -loglevel quiet')
                    
                    vc.play(source)
                    print(f"▶️ Playing TTS in {vc.channel.name}", flush=True)
                    
                    # Cleanup after
                    while vc.is_playing():
                        await asyncio.sleep(0.5)
                    
                    try:
                        os.remove(tmp)
                    except:
                        pass
                    
                    print(f"✅ TTS played", flush=True)
                except Exception as e:
                    print(f"⚠️ TTS fail (text still works): {e}", flush=True)

    except Exception as e:
        print(f"⚠️ Voice TTS error (text still works): {e}", flush=True)

@bot.command(name="join")
async def join_cmd(ctx):
    """Join VC - for voice TTS"""
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
            await ctx.send(f"✅ Joined {ch.mention}\nText notification 100% kaj korbe, voice TTS try korbe!")
    except Exception as e:
        await ctx.send(f"❌ Join fail: {e}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left VC")
    else:
        await ctx.send("❌ VC te nai")

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
    
    try:
        from gtts import gTTS
        import uuid as uuid_lib
        tmp = f"/tmp/tts_{uuid_lib.uuid4().hex}.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(tmp)
        
        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.5)
        
        ffmpeg_exe = FFMPEG_EXE or shutil.which("ffmpeg")
        if ffmpeg_exe:
            source = discord.FFmpegPCMAudio(tmp, executable=ffmpeg_exe, options='-vn -loglevel quiet')
        else:
            source = discord.FFmpegPCMAudio(tmp, options='-vn -loglevel quiet')
        
        await ctx.send(f"🗣️ Bolchi: {text}")
        vc.play(source)
        
        while vc.is_playing():
            await asyncio.sleep(0.5)
        
        try:
            os.remove(tmp)
        except:
            pass
        
    except Exception as e:
        await ctx.send(f"❌ TTS fail: {e}")

@bot.command(name="test")
async def test_cmd(ctx):
    ch = await get_text_channel_async(ctx.guild)
    if not ch:
        await ctx.send(f"❌ No notification channel for this server! Set env NOTIFICATION_CHANNELS with {ctx.guild.id}:<channel_id>")
        return
    embed = discord.Embed(title="✅ Test", description=f"Test by {ctx.author.mention}\nGuild: {ctx.guild.name}", color=discord.Color.green())
    await ch.send(embed=embed)
    await ctx.send(f"✅ Sent to {ch.mention}")

@bot.command(name="debug")
async def debug_cmd(ctx):
    ch = await get_text_channel_async(ctx.guild)
    vc = ctx.voice_client
    await ctx.send(f"""
**FINAL DEBUG**
Guild: {ctx.guild.name} ({ctx.guild.id})
Text Channel: {ch.name if ch else 'NOT SET ❌'} ({ch.id if ch else 'N/A'})
Your VC: {ctx.author.voice.channel.name if ctx.author.voice else 'Not in VC'}
Bot VC: {vc.channel.name if vc else 'Not in VC'}
FFmpeg: {FFMPEG_EXE or 'NOT FOUND'}
Opus: {discord.opus.is_loaded()}
Text 100%: {'✅ YES' if ch else '❌ Set env'}
Voice TTS: {'✅ May work' if FFMPEG_EXE else '❌ FFmpeg missing'}
""")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | Text: 100% | Voice: {'✅' if FFMPEG_EXE else '❌'}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 WHITE_WOLF FINAL BOT", description="Text 100% + Voice TTS", color=discord.Color.green())
    embed.add_field(name="✅ Text (100% Render)", value="Auto: Join/Leave/Move text channel e bolbe\n`!test` - Test text", inline=False)
    embed.add_field(name="🎙️ Voice (Local 100%, Render may work)", value="`!join` - VC te join\n`!say <text>` - Voice e bolao\n`!leave` - Leave", inline=False)
    embed.add_field(name="Multi-Server", value="Env `NOTIFICATION_CHANNELS`:\n`{\"guild_id\": channel_id, \"guild2\": channel2}`\nBa `guild:channel,guild:channel`", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting FINAL BOT - Text 100% + Voice TTS...", flush=True)
    bot.run(TOKEN)
