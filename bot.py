"""
🐺 WHITE_WOLF Voice Notification Bot - ORIGINAL SIMPLE VERSION (100% Working)
Ager moto - kew join korle text channel e naam dhore bolbe
+ Render port fix

Original logic + http.server keep-alive for Render
"""

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | CHANNEL_ID={NOTIFICATION_CHANNEL_ID_RAW} | PORT={PORT}", flush=True)

if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN missing! Render Environment e add koro')

try:
    NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID_RAW) if NOTIFICATION_CHANNEL_ID_RAW else 0
except:
    raise ValueError(f"❌ NOTIFICATION_CHANNEL_ID must be number, got {NOTIFICATION_CHANNEL_ID_RAW}")

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID missing!')

# ========== RENDER WEB SERVER (Port binding fix) ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Bot Running')
        else:
            self.wfile.write(b'WHITE_WOLF Voice Bot Alive - Text Notification Ready')
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Starting web server on 0.0.0.0:{PORT}...", flush=True)
        httpd = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ WEB SERVER LISTENING on 0.0.0.0:{PORT} - Render will detect port", flush=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"❌ Web server error: {e}", flush=True)

threading.Thread(target=start_web, daemon=True).start()
time.sleep(1)
print("✅ Web server started, starting bot...", flush=True)

# ========== ORIGINAL BOT LOGIC (Simple & Working) ==========
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
    print(f'🤖 Logged in as: {bot.user} (ID: {bot.user.id})', flush=True)
    print(f'🔔 Notification Channel ID: {NOTIFICATION_CHANNEL_ID}', flush=True)
    print(f'🌐 Servers: {len(bot.guilds)}', flush=True)
    for guild in bot.guilds:
        print(f'   - {guild.name} ({guild.id})', flush=True)
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f'      ✅ Found #{ch.name} in {guild.name}', flush=True)
            perms = ch.permissions_for(guild.me)
            print(f'      Perms: View={perms.view_channel} Send={perms.send_messages} Embed={perms.embed_links}', flush=True)
    print('===================================', flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

    # Startup test
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        print(f"📨 Sending startup test to #{channel.name}", flush=True)
        embed = discord.Embed(
            title='🟢 Bot Online!',
            description='✅ Voice notification active!\nKew voice e join/leave korle ami bolbo 🐺',
            color=discord.Color.green()
        )
        embed.set_footer(text='WHITE_WOLF GLOBAL • Original Simple Version')
        await channel.send(embed=embed)
        print("✅ Startup message sent!", flush=True)
    except Exception as e:
        print(f"❌ Startup message failed: {e}", flush=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | Guild: {member.guild.name}", flush=True)

    # Find notification channel - ORIGINAL LOGIC
    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        except Exception as e:
            print(f'❌ Channel not found ID {NOTIFICATION_CHANNEL_ID}: {e}', flush=True)
            return

    if channel is None:
        print(f"❌ No channel for ID {NOTIFICATION_CHANNEL_ID}", flush=True)
        return

    try:
        if before.channel is None and after.channel is not None:
            # JOINED - ORIGINAL SIMPLE EMBED
            print(f"   -> JOIN: {member.display_name} -> {after.channel.name}", flush=True)
            embed = discord.Embed(
                title='🎙️ Voice Channel Joined',
                description=f'**{member.display_name}** just joined the voice channel!',
                color=discord.Color.green()
            )
            embed.add_field(name='👤 Member', value=member.mention, inline=True)
            embed.add_field(name='🔊 Channel', value=after.channel.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
            await channel.send(embed=embed)
            print(f"   -> ✅ Join notification sent to #{channel.name}", flush=True)

        elif before.channel is not None and after.channel is None:
            # LEFT
            print(f"   -> LEAVE: {member.display_name} <- {before.channel.name}", flush=True)
            embed = discord.Embed(
                title='👋 Voice Channel Left',
                description=f'**{member.display_name}** left the voice channel.',
                color=discord.Color.red()
            )
            embed.add_field(name='👤 Member', value=member.mention, inline=True)
            embed.add_field(name='🔊 Channel', value=before.channel.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
            await channel.send(embed=embed)
            print(f"   -> ✅ Leave notification sent", flush=True)

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            # MOVED
            print(f"   -> MOVE: {member.display_name} {before.channel.name} -> {after.channel.name}", flush=True)
            embed = discord.Embed(
                title='🔄 Voice Channel Moved',
                description=f'**{member.display_name}** moved to another voice channel.',
                color=discord.Color.blue()
            )
            embed.add_field(name='👤 Member', value=member.mention, inline=False)
            embed.add_field(name='⬅️ From', value=before.channel.mention, inline=True)
            embed.add_field(name='➡️ To', value=after.channel.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
            await channel.send(embed=embed)
            print(f"   -> ✅ Move notification sent", flush=True)

    except discord.Forbidden:
        print(f"❌ FORBIDDEN: No permission in #{channel.name}", flush=True)
    except Exception as e:
        print(f"❌ Voice error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# Simple commands for testing
@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms | Original Simple Bot 🐺")

@bot.command(name="test")
async def test_cmd(ctx):
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        embed = discord.Embed(
            title='✅ Test Notification',
            description=f'Test by {ctx.author.mention} - Channel ID correct!',
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await ctx.send(f"✅ Sent to {channel.mention}")
        print(f"✅ !test sent to #{channel.name}", flush=True)
    except Exception as e:
        await ctx.send(f"❌ {e}")
        print(f"❌ !test fail: {e}", flush=True)

@bot.command(name="debug")
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    perms = ctx.channel.permissions_for(ctx.guild.me) if ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID) else None
    await ctx.send(f"""
**DEBUG - Original Simple Bot**
Guild: {ctx.guild.name}
ENV Channel ID: {NOTIFICATION_CHANNEL_ID}
Found in this guild: {ch.name if ch else 'NOT FOUND ❌'}
Bot perms in notif channel: View={ch.permissions_for(ctx.guild.me).view_channel if ch else 'N/A'} Send={ch.permissions_for(ctx.guild.me).send_messages if ch else 'N/A'}
Latency: {round(bot.latency*1000)}ms
""")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting ORIGINAL SIMPLE Bot - 100% Working Version...", flush=True)
    bot.run(TOKEN)
