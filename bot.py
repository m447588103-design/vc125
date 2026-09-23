"""
🐺 WHITE_WOLF Voice TTS Bot - LOCAL + RENDER BOTH WORKING
Tumi local e TTS use kore kaj koraiso, eita sei logic + Render port fix
Kew join korle bot VC te join hoye SOUND diye bolbe "X join korse"
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

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | TEXT_FB={NOTIFICATION_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# Check FFmpeg
ffmpeg_path = shutil.which("ffmpeg")
print(f"🔍 FFmpeg: {ffmpeg_path} | Opus loaded: {discord.opus.is_loaded()}", flush=True)

# ========== RENDER WEB SERVER (Only addition for Render, local e problem korbe na) ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - TTS Bot Running')
        else:
            self.wfile.write(b'WHITE_WOLF TTS Bot Alive')
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

# Start web server in background - local e o cholbe, Render e must
threading.Thread(target=start_web, daemon=True).start()
time.sleep(1)

# ========== DISCORD BOT - TTS LOGIC (Tomar local e kaj kora logic) ==========
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Simple lock to prevent overlapping speech
voice_lock = asyncio.Lock()

async def tts_speak(guild, channel, text):
    """
    TTS - Local e kaj kora simple logic
    gTTS diye mp3 banabe, FFmpeg diye bajabe
    """
    async with voice_lock:
        try:
            # Ensure bot in VC
            vc = guild.voice_client
            if vc is None:
                print(f"🔊 Joining {channel.name} to speak: {text}", flush=True)
                vc = await channel.connect()
            elif vc.channel.id != channel.id:
                print(f"🔄 Moving to {channel.name}", flush=True)
                await vc.move_to(channel)
            
            # Generate TTS file
            tmp_file = f"/tmp/tts_{uuid.uuid4().hex}.mp3"
            print(f"🗣️ gTTS: '{text}' -> {tmp_file}", flush=True)
            
            # gTTS - simple, local e kaj kore
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(tmp_file)
            
            print(f"✅ TTS saved, size: {os.path.getsize(tmp_file)} bytes", flush=True)
            
            # Play with FFmpeg
            if vc.is_playing():
                vc.stop()
                await asyncio.sleep(0.5)
            
            print(f"▶️ Playing: {text}", flush=True)
            source = discord.FFmpegPCMAudio(tmp_file)
            vc.play(source)
            
            # Wait till done
            while vc.is_playing():
                await asyncio.sleep(0.5)
            
            print(f"✅ Done: {text}", flush=True)
            
            # Cleanup
            try:
                os.remove(tmp_file)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ TTS Error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Cleanup
            try:
                if 'tmp_file' in locals() and os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except:
                pass
            return False

@bot.event
async def on_ready():
    print(f"\n{'='*60}\n🐺 TTS BOT ONLINE! {bot.user}\nGuilds: {len(bot.guilds)} | FFmpeg: {bool(ffmpeg_path)}\n{'='*60}\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Voice TTS | !join"))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel}", flush=True)

    try:
        # JOIN - Bot VC te join hoye bolbe
        if before.channel is None and after.channel is not None:
            text = f"{member.display_name} joined {after.channel.name}"
            # Bangla chaile: f"{member.display_name} voice e join korse"
            # Tumi chaile Bangla koro, ami English rakhlam - tumi change korte parba
            # Bangla version:
            text_bn = f"{member.display_name} voice e join korse"
            
            print(f"   -> JOIN: {text_bn}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text_bn)
            
            # Text fallback o pathabe jodi channel ID thake
            if NOTIFICATION_CHANNEL_ID:
                try:
                    ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                    if not ch:
                        ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
                    embed = discord.Embed(title="🎙️ Joined", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
                    await ch.send(embed=embed)
                except:
                    pass

        # LEAVE
        elif before.channel is not None and after.channel is None:
            text_bn = f"{member.display_name} voice theke leave nise"
            print(f"   -> LEAVE: {text_bn}", flush=True)
            
            vc = member.guild.voice_client
            if vc and vc.channel.id == before.channel.id:
                await tts_speak(member.guild, before.channel, text_bn)
                # Check if empty, then leave after 10 sec
                await asyncio.sleep(2)
                if len(before.channel.members) == 1:  # Only bot left
                    await asyncio.sleep(8)
                    if len(before.channel.members) == 1:
                        try:
                            await vc.disconnect()
                            print(f"   -> Left empty {before.channel.name}", flush=True)
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

        # MOVE
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            text_bn = f"{member.display_name} {after.channel.name} e move korse"
            print(f"   -> MOVE: {text_bn}", flush=True)
            await asyncio.sleep(0.5)
            await tts_speak(member.guild, after.channel, text_bn)

    except Exception as e:
        print(f"❌ Voice event error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# ========== COMMANDS ==========
@bot.command(name="join")
async def join_cmd(ctx):
    """VC te join - local e kaj kora simple logic"""
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
        print(f"❌ Join fail: {e}", flush=True)

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="say")
async def say_cmd(ctx, *, text: str):
    """Tomar deya text voice e bolbe - !say Hello"""
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
    """TTS test - local e kaj kora logic"""
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ Age VC te join koro, tarpor !join")
            return
    
    await ctx.send("🎙️ Testing TTS...")
    await tts_speak(ctx.guild, ctx.voice_client.channel, f"{ctx.author.display_name} voice e join korse")
    await ctx.send("✅ Jodi voice e sunte paiso, TTS kaj kore!")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(ffmpeg_path)} | VC: {bool(ctx.voice_client)}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 TTS Voice Bot", description="Local + Render both working", color=discord.Color.green())
    embed.add_field(name="Auto", value="Join korle VC te ese bolbe\nLeave nile bolbe", inline=False)
    embed.add_field(name="Commands", value="`!join` - VC te ano\n`!leave` - Ber hobe\n`!say <text>` - Bolao\n`!testvoice` - Test\n`!ping` - Ping", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting TTS Bot - Local + Render Working...", flush=True)
    bot.run(TOKEN)
