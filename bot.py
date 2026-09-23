"""
🐺 WHITE_WOLF KITT Bot - FINAL Render Ready Version
✅ 100% Render Free Tier Working - Tested
- http.server (stdlib) - no Flask, no aiohttp needed - instant port bind
- KITT style: naam dhore bolbe join/leave
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
CHANNEL_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | CHANNEL={CHANNEL_RAW} | PORT={PORT}", flush=True)

if not TOKEN:
    raise ValueError("DISCORD_TOKEN missing! Render Environment e add koro")
try:
    NOTIFICATION_CHANNEL_ID = int(CHANNEL_RAW) if CHANNEL_RAW else 0
except:
    raise ValueError(f"CHANNEL_ID must be number, got {CHANNEL_RAW}")
if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError("NOTIFICATION_CHANNEL_ID missing!")

# ========== RENDER WEB SERVER (MOST IMPORTANT) ==========
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'OK - Bot Running')
        else:
            self.wfile.write(b'WHITE_WOLF KITT Bot Alive - Voice Logger Ready')
    def log_message(self, format, *args):
        return

def start_web():
    try:
        print(f"🌐 Starting web server on 0.0.0.0:{PORT}...", flush=True)
        httpd = HTTPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ WEB SERVER LISTENING on 0.0.0.0:{PORT} - Render will detect port!", flush=True)
        httpd.serve_forever()
    except Exception as e:
        print(f"❌ Web server error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# Start BEFORE bot - Render needs port in 60s
web_thread = threading.Thread(target=start_web, daemon=True)
web_thread.start()
print("🌐 Web thread started, waiting 1s for bind...", flush=True)
time.sleep(1)

# ========== DISCORD BOT ==========
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"\n{'='*50}\n🐺 KITT BOT ONLINE! {bot.user}\n🔔 Channel ID: {NOTIFICATION_CHANNEL_ID}\nGuilds: {len(bot.guilds)}\n{'='*50}\n", flush=True)
    for g in bot.guilds:
        ch = g.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f"✅ Found #{ch.name} in {g.name}", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="WHITE_WOLF GLOBAL"))

    try:
        ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not ch:
            ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        embed = discord.Embed(
            title="🟢 KITT Bot Online!",
            description="✅ **Render Deploy Success!**\nAmi ready! Kew voice e asle naam dhore bolbo 🐺",
            color=discord.Color.green()
        )
        embed.add_field(name="🎙️ Join", value="Join korse bolbo", inline=True)
        embed.add_field(name="👋 Leave", value="Leave nise bolbo", inline=True)
        embed.add_field(name="🔄 Move", value="Move korle bolbo", inline=True)
        await ch.send(embed=embed)
        print("✅ Startup message sent!", flush=True)
    except Exception as e:
        print(f"❌ Startup msg fail: {e}", flush=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel}", flush=True)
    
    ch = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if not ch:
        ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not ch:
        try:
            ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        except:
            return
    if not ch:
        return

    try:
        avatar = member.display_avatar.url
    except:
        avatar = None

    try:
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🎙️ Voice e Join Korse!",
                description=f"**{member.display_name}** voice e **join korse**!",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Member", value=f"{member.mention}", inline=True)
            embed.add_field(name="🔊 Channel", value=f"{after.channel.mention}", inline=True)
            embed.add_field(name="📢", value=f"**{member.display_name}** joined **{after.channel.name}**", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="WHITE_WOLF GLOBAL • KITT Bot")
            await ch.send(embed=embed)

        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="👋 Voice Theke Leave Nise!",
                description=f"**{member.display_name}** voice theke **leave nise**!",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Member", value=f"{member.mention}", inline=True)
            embed.add_field(name="🔊 Channel", value=f"{before.channel.mention}", inline=True)
            embed.add_field(name="📢", value=f"**{member.display_name}** left **{before.channel.name}**", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="WHITE_WOLF GLOBAL • KITT Bot")
            await ch.send(embed=embed)

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            embed = discord.Embed(
                title="🔄 Channel Change Korse!",
                description=f"**{member.display_name}** channel change korse!",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤", value=member.mention, inline=False)
            embed.add_field(name="⬅️ From", value=before.channel.mention, inline=True)
            embed.add_field(name="➡️ To", value=after.channel.mention, inline=True)
            embed.add_field(name="📢", value=f"**{member.display_name}** moved {before.channel.name} -> {after.channel.name}", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="WHITE_WOLF GLOBAL • KITT Bot")
            await ch.send(embed=embed)
    except Exception as e:
        print(f"❌ Voice send error: {e}", flush=True)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong {round(bot.latency*1000)}ms | KITT Online 🐺")

@bot.command(name="test")
async def test_cmd(ctx):
    try:
        ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not ch:
            ch = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        await ctx.send(f"Testing -> {ch.mention}")
        embed = discord.Embed(title="🎙️ Voice e Join Korse! (TEST)", description=f"**{ctx.author.display_name}** join korse! (Test)", color=discord.Color.green())
        embed.add_field(name="Member", value=ctx.author.mention, inline=True)
        await ch.send(embed=embed)
        await ctx.send(f"✅ Check {ch.mention}")
    except Exception as e:
        await ctx.send(f"❌ {e}")

@bot.command(name="debug")
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    perms = ctx.channel.permissions_for(ctx.guild.me)
    await ctx.send(f"**DEBUG**\nGuild: {ctx.guild.name}\nChannel ENV: {NOTIFICATION_CHANNEL_ID}\nFound: {ch.name if ch else 'NOT FOUND'}\nPerms: View={perms.view_channel} Send={perms.send_messages} Embed={perms.embed_links}")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 KITT Bot Help", color=discord.Color.gold())
    embed.add_field(name="Auto", value="Join korle bolbe\nLeave nile bolbe\nMove korle bolbe", inline=False)
    embed.add_field(name="Commands", value="!ping !test !debug !help", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Starting KITT Bot...", flush=True)
    bot.run(TOKEN)
