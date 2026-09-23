import os
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

print(f"🔧 ENV CHECK: TOKEN exists? {bool(TOKEN)} | CHANNEL_ID: {NOTIFICATION_CHANNEL_ID_RAW} | PORT: {PORT}", flush=True)

if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN missing! Render Dashboard > Environment e add koro.')

try:
    NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID_RAW) if NOTIFICATION_CHANNEL_ID_RAW else 0
except ValueError:
    raise ValueError(f'❌ NOTIFICATION_CHANNEL_ID must be number, got: {NOTIFICATION_CHANNEL_ID_RAW}')

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID missing!')

# --- HTTP Keep-Alive Server for Render (100% reliable) ---
# Flask er bodole http.server use korlam karon Render Flask thread detect korte pare na
# Eta instant 0.0.0.0:PORT e bind hoye jay

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Bot is running')
        else:
            self.wfile.write(b'🐺 WHITE_WOLF Voice Bot is Alive! ✅')
    
    def log_message(self, format, *args):
        # Render log spam komanor jonno http log off
        return

def run_http_server():
    try:
        print(f"🌐 Starting HTTP server on 0.0.0.0:{PORT}...", flush=True)
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        print(f"✅ HTTP server listening on 0.0.0.0:{PORT} - Render will detect this port", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ HTTP server failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

# Start HTTP server in daemon thread BEFORE bot starts
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()
print(f"🌐 Keep-alive thread started, waiting 2s for port bind...", flush=True)
time.sleep(2)  # Render ke port detect korar time dao
print(f"✅ Port should be bound now, starting Discord bot...", flush=True)

# --- Discord Bot ---
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('===================================', flush=True)
    print('🐺 WHITE_WOLF Voice Bot Online', flush=True)
    print(f'🤖 {bot.user} (ID: {bot.user.id})', flush=True)
    print(f'🔔 Target Channel ID: {NOTIFICATION_CHANNEL_ID}', flush=True)
    print(f'🌐 Guilds: {len(bot.guilds)}', flush=True)
    for guild in bot.guilds:
        print(f'   - {guild.name} ({guild.id})', flush=True)
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f'      ✅ FOUND #{ch.name} | View={ch.permissions_for(guild.me).view_channel} Send={ch.permissions_for(guild.me).send_messages} Embed={ch.permissions_for(guild.me).embed_links}', flush=True)
    print('===================================', flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

    # Startup test message
    print("📨 Sending startup message...", flush=True)
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            print("   -> get_channel None, trying fetch...", flush=True)
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        print(f"   -> Channel: {channel} | Guild: {channel.guild.name}", flush=True)
        await channel.send("🟢 **WHITE_WOLF Bot Online!** Voice log active ✅\nRender port binding fixed!")
        print("✅ Startup message sent!", flush=True)
    except discord.Forbidden:
        print(f"❌ FORBIDDEN: Permission nai #{NOTIFICATION_CHANNEL_ID} e", flush=True)
    except discord.NotFound:
        print(f"❌ NOT FOUND: Channel ID {NOTIFICATION_CHANNEL_ID} vul!", flush=True)
    except Exception as e:
        print(f"❌ Startup send failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

@bot.command(name='ping')
async def ping_cmd(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency*1000)}ms | 🟢 Online')

@bot.command(name='test')
async def test_cmd(ctx):
    print(f"[CMD] !test by {ctx.author}", flush=True)
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        await ctx.send(f"🔍 Sending to {channel.mention}...")
        await channel.send(f"✅ Test from {ctx.author.mention} - Works!")
        
        embed = discord.Embed(title='✅ Test Embed', description=f'Triggered by {ctx.author.mention}', color=discord.Color.green())
        embed.add_field(name='Channel ID', value=f'`{NOTIFICATION_CHANNEL_ID}`', inline=True)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Sent to {channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed: {e}")
        print(f"❌ !test failed: {e}", flush=True)

@bot.command(name='debug')
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    info = f"""**DEBUG**
Guild: {ctx.guild.name} ({ctx.guild.id})
This Channel: {ctx.channel.name} ({ctx.channel.id})
ENV ID: `{NOTIFICATION_CHANNEL_ID}`
guild.get_channel: {ch.name if ch else 'None'}
Bot perms: View={ctx.channel.permissions_for(ctx.guild.me).view_channel} Send={ctx.channel.permissions_for(ctx.guild.me).send_messages}
"""
    await ctx.send(info)

@bot.event
async def on_voice_state_update(member, before, after):
    print(f"\n[VOICE] {member.display_name} | {before.channel} -> {after.channel} | guild={member.guild.name}", flush=True)
    if member.bot:
        print("   -> Skip bot", flush=True)
        return

    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        except Exception as e:
            print(f"❌ Channel fetch failed: {e}", flush=True)
            return

    if channel is None:
        print(f"❌ No channel for ID {NOTIFICATION_CHANNEL_ID}", flush=True)
        return

    print(f"   -> Target: #{channel.name}", flush=True)

    try:
        avatar_url = member.display_avatar.url if member.display_avatar else None
    except:
        avatar_url = None

    try:
        if before.channel is None and after.channel is not None:
            print("   -> JOIN", flush=True)
            embed = discord.Embed(title='🎙️ Voice Joined', description=f'**{member.display_name}** joined {after.channel.mention}', color=discord.Color.green())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=after.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL')
            await channel.send(embed=embed)
            print("   -> ✅ Sent", flush=True)

        elif before.channel is not None and after.channel is None:
            print("   -> LEAVE", flush=True)
            embed = discord.Embed(title='👋 Voice Left', description=f'**{member.display_name}** left {before.channel.mention}', color=discord.Color.red())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=before.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL')
            await channel.send(embed=embed)
            print("   -> ✅ Sent", flush=True)

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            print(f"   -> MOVE {before.channel.name} -> {after.channel.name}", flush=True)
            embed = discord.Embed(title='🔄 Voice Moved', description=f'**{member.display_name}** moved', color=discord.Color.blue())
            embed.add_field(name='From', value=before.channel.mention, inline=True)
            embed.add_field(name='To', value=after.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL')
            await channel.send(embed=embed)
            print("   -> ✅ Sent", flush=True)
        else:
            print("   -> Ignored (mute/deafen)", flush=True)

    except discord.Forbidden as e:
        print(f"❌ FORBIDDEN: {e}", flush=True)
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}", flush=True)
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting bot...", flush=True)
    bot.run(TOKEN, log_handler=None)
