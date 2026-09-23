"""
FINAL FIX - VC Join Issue + Text Fallback
Bot VC te join na nile text e bolbe + permission check
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
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNEL_ID')
if NOTIFICATION_CHANNEL_ID:
    try:
        NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID)
    except:
        NOTIFICATION_CHANNEL_ID = None

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | PORT={PORT} | TEXT_CH={NOTIFICATION_CHANNEL_ID}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing!")

# Check deps
print("🔍 Checking deps...", flush=True)
ffmpeg_path = shutil.which("ffmpeg")
print(f"FFmpeg: {ffmpeg_path}", flush=True)
try:
    import nacl
    print(f"✅ PyNaCl: {nacl.__version__}", flush=True)
except Exception as e:
    print(f"❌ PyNaCl missing: {e}", flush=True)

# Opus
try:
    if not discord.opus.is_loaded():
        # Try common opus lib names on Render (Ubuntu)
        for lib in ['libopus.so.0', 'libopus.so', 'libopus.so.1', 'opus']:
            try:
                discord.opus.load_opus(lib)
                print(f"✅ Opus loaded: {lib}", flush=True)
                break
            except:
                continue
    print(f"Opus loaded: {discord.opus.is_loaded()}", flush=True)
except Exception as e:
    print(f"⚠️ Opus check: {e}", flush=True)

# Web server
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK')
        else:
            self.wfile.write(f"Bot Alive | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()}".encode())
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
    print(f"\n{'='*60}\n🐺 BOT ONLINE! {bot.user}\nFFmpeg: {ffmpeg_path} | Opus: {discord.opus.is_loaded()} | Guilds: {len(bot.guilds)}\n{'='*60}\n", flush=True)
    for g in bot.guilds:
        print(f" - {g.name} ({g.id}) | Members: {g.member_count}", flush=True)
        # Check bot permissions in guild
        me = g.me
        print(f"   Bot perms: {me.guild_permissions}", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!join | !help"))

@bot.event
async def on_voice_state_update(member, before, after):
    print(f"[VOICE] {member.display_name} bot={member.bot} | {before.channel} -> {after.channel} | {member.guild.name}", flush=True)
    
    if member.id == bot.user.id:
        if before.channel is None and after.channel is not None:
            print(f"   🤖 BOT JOINED {after.channel.name}", flush=True)
        elif before.channel is not None and after.channel is None:
            print(f"   🤖 BOT LEFT {before.channel.name}", flush=True)
        return
    
    if member.bot:
        return

    # Text fallback - always send text if NOTIFICATION_CHANNEL_ID set
    if NOTIFICATION_CHANNEL_ID:
        try:
            ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if not ch:
                ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
            
            if before.channel is None and after.channel is not None:
                embed = discord.Embed(title="🎙️ Voice Join", description=f"**{member.display_name}** joined **{after.channel.name}**", color=discord.Color.green())
                embed.add_field(name="Member", value=member.mention, inline=True)
                embed.add_field(name="Channel", value=after.channel.mention, inline=True)
                await ch.send(embed=embed)
                print(f"   -> Text notification sent to #{ch.name}", flush=True)
            elif before.channel is not None and after.channel is None:
                embed = discord.Embed(title="👋 Voice Leave", description=f"**{member.display_name}** left **{before.channel.name}**", color=discord.Color.red())
                await ch.send(embed=embed)
            elif before.channel and after.channel and before.channel.id != after.channel.id:
                embed = discord.Embed(title="🔄 Voice Move", description=f"**{member.display_name}** moved {before.channel.name} -> {after.channel.name}", color=discord.Color.blue())
                await ch.send(embed=embed)
        except Exception as e:
            print(f"   -> Text fallback error: {e}", flush=True)

@bot.command(name="join")
async def join_cmd(ctx):
    """VC te join with full permission check"""
    print(f"\n🔊 !join by {ctx.author} in {ctx.guild.name}", flush=True)
    
    if not ctx.author.voice:
        await ctx.send("❌ Tumi kono VC te nai! Age ekta voice channel e join koro, tarpor `!join` likho")
        return
    
    vc_channel = ctx.author.voice.channel
    print(f"   Target VC: {vc_channel.name} ({vc_channel.id})", flush=True)
    
    # Permission check
    perms = vc_channel.permissions_for(ctx.guild.me)
    print(f"   Bot perms in {vc_channel.name}: Connect={perms.connect} Speak={perms.speak} View={perms.view_channel} UseVoice={perms.use_voice_activation}", flush=True)
    
    if not perms.view_channel:
        await ctx.send(f"❌ Amar {vc_channel.mention} dekhar permission nai! Channel Settings > Permissions > Bot ke View Channel dao")
        return
    if not perms.connect:
        await ctx.send(f"❌ Amar {vc_channel.mention} e Connect er permission nai! Permissions e Connect ON koro")
        return
    if not perms.speak:
        await ctx.send(f"❌ Amar {vc_channel.mention} e Speak er permission nai! Permissions e Speak ON koro")
        return
    
    # Check Opus and FFmpeg
    if not discord.opus.is_loaded():
        await ctx.send("❌ Opus not loaded! Voice kaj korbe na. Render log e Opus error dekho")
        print("❌ Opus not loaded, cannot join VC", flush=True)
        return
    
    if not ffmpeg_path:
        await ctx.send("⚠️ FFmpeg not found, but trying to join anyway... Voice e kotha bolte parbo na, but join hobo")
    
    try:
        existing_vc = ctx.voice_client
        if existing_vc:
            if existing_vc.channel.id == vc_channel.id:
                await ctx.send(f"✅ Already in {vc_channel.mention} | Connected: {existing_vc.is_connected()}")
                print(f"   Already in {vc_channel.name}", flush=True)
                return
            else:
                print(f"   Moving from {existing_vc.channel.name} to {vc_channel.name}", flush=True)
                await existing_vc.move_to(vc_channel)
                await ctx.send(f"✅ Moved to {vc_channel.mention}")
                return
        else:
            print(f"   Connecting to {vc_channel.name}...", flush=True)
            # Try with timeout and no self deaf/mute
            vc = await vc_channel.connect(timeout=15, self_deaf=False)
            print(f"✅ Connected! VC: {vc} | Channel: {vc.channel.name} | Connected: {vc.is_connected()}", flush=True)
            await ctx.send(f"✅ **Joined {vc_channel.mention}**\nConnected: {vc.is_connected()}\nFFmpeg: {ffmpeg_path}\nOpus: {discord.opus.is_loaded()}\n\nEkhon kew VC te join/leave korle text e notification jabe. Voice TTS er jonno `!testvoice` try koro (jodi FFmpeg thake)")
            
            # Keep alive check
            await asyncio.sleep(2)
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await ctx.send("❌ Bot 2 sec er moddhe disconnect hoye gese! Render voice UDP block korte pare. Text notification kaj korbe.")
                print("❌ Disconnected quickly after join", flush=True)
            
    except discord.errors.ClientException as e:
        print(f"❌ ClientException: {e}", flush=True)
        await ctx.send(f"❌ Join failed (ClientException): {e}\nAmi hoyto already onno VC te achi. `!leave` diye ber hoye abar `!join` koro")
    except discord.errors.Forbidden as e:
        print(f"❌ Forbidden: {e}", flush=True)
        await ctx.send(f"❌ Forbidden: {e}\nPermission nai!")
    except Exception as e:
        print(f"❌ Join error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        await ctx.send(f"❌ Join failed: {e}\nCheck Render logs for details\nFFmpeg: {ffmpeg_path}\nOpus: {discord.opus.is_loaded()}")

@bot.command(name="leave")
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left VC")
    else:
        await ctx.send("❌ VC te nai")

@bot.command(name="debug")
async def debug_cmd(ctx):
    vc = ctx.voice_client
    user_vc = ctx.author.voice.channel if ctx.author.voice else None
    
    # Perms check
    if user_vc:
        perms = user_vc.permissions_for(ctx.guild.me)
        perm_text = f"View={perms.view_channel} Connect={perms.connect} Speak={perms.speak}"
    else:
        perm_text = "User not in VC"
    
    msg = f"""
**🔍 DEBUG**
**Guild:** {ctx.guild.name}
**You in VC:** {user_vc.name if user_vc else 'No'}
**Bot in VC:** {vc.channel.name if vc else 'No'} | Connected: {vc.is_connected() if vc else False}
**Bot Perms in your VC:** {perm_text}
**FFmpeg:** {ffmpeg_path or 'NOT FOUND'}
**Opus Loaded:** {discord.opus.is_loaded()}
**PyNaCl:** Installed
**Text Channel ID:** {NOTIFICATION_CHANNEL_ID}
**Latency:** {round(bot.latency*1000)}ms
"""
    await ctx.send(msg)
    print(msg, flush=True)

@bot.command(name="testtext")
async def testtext_cmd(ctx):
    """Test text notification"""
    if not NOTIFICATION_CHANNEL_ID:
        await ctx.send("❌ NOTIFICATION_CHANNEL_ID env set koro Render e, text notification er jonno")
        return
    try:
        ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not ch:
            ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        embed = discord.Embed(title="✅ Test Text", description=f"Test by {ctx.author.mention}", color=discord.Color.green())
        await ch.send(embed=embed)
        await ctx.send(f"✅ Sent to {ch.mention}")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 {round(bot.latency*1000)}ms | FFmpeg: {bool(ffmpeg_path)} | Opus: {discord.opus.is_loaded()} | VC: {bool(ctx.voice_client)}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 WHITE_WOLF Bot - Help", color=discord.Color.gold())
    embed.add_field(name="Voice (Debug)", value="`!join` - VC te join\n`!leave` - Leave\n`!debug` - Full debug", inline=False)
    embed.add_field(name="Text Notification", value="`!testtext` - Text channel e test\nAuto: Join/Leave/Move text e bolbe (jodi NOTIFICATION_CHANNEL_ID set thake)", inline=False)
    embed.add_field(name="Fix for VC not joining", value="1. Bot role ke Connect+Speak dao\n2. Channel e bot ke View+Connect+Speak dao\n3. `!debug` e perms check koro", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting Bot - VC Join Fix + Text Fallback...", flush=True)
    bot.run(TOKEN)
