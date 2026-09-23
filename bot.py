"""
🐺 WHITE_WOLF Voice Notification Bot - Render Ready V2
100% Render Free Tier compatible - No Flask, No Threading issues
Uses aiohttp web server in same asyncio loop as Discord bot
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from aiohttp import web

load_dotenv()

# ========== CONFIG ==========
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

print(f"🔧 CONFIG CHECK: TOKEN={bool(TOKEN)} | CHANNEL_ID={CHANNEL_ID_RAW} | PORT={PORT}", flush=True)

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN missing! Render > Environment e add koro")

try:
    NOTIFICATION_CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else 0
except:
    raise ValueError(f"❌ NOTIFICATION_CHANNEL_ID must be number, got: {CHANNEL_ID_RAW}")

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError("❌ NOTIFICATION_CHANNEL_ID missing!")

# ========== DISCORD SETUP ==========
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Portal e ON must
intents.voice_states = True
intents.message_content = True  # ! commands er jonno

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ========== WEB SERVER (Render needs open port) ==========
async def health_handler(request):
    return web.Response(text="OK - WHITE_WOLF Bot is Running 🐺", status=200)

async def home_handler(request):
    return web.Response(
        text="🐺 WHITE_WOLF Voice Bot is Alive! ✅\n\nEndpoints:\n/ -> This page\n/health -> Health check for Render\n\nBot is running 24/7",
        status=200,
        content_type="text/plain"
    )

async def start_web_server():
    """Render er jonno port bind kora must, naile kill kore dey"""
    app = web.Application()
    app.router.add_get('/', home_handler)
    app.router.add_get('/health', health_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"✅ WEB SERVER started on 0.0.0.0:{PORT} - Render will detect port now!", flush=True)
    print(f"🌐 Health check: http://0.0.0.0:{PORT}/health", flush=True)
    return runner

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    print("\n" + "="*50, flush=True)
    print("🐺 WHITE_WOLF Voice Bot Online!", flush=True)
    print(f"🤖 Logged in as: {bot.user} (ID: {bot.user.id})", flush=True)
    print(f"🔔 Notification Channel ID: {NOTIFICATION_CHANNEL_ID}", flush=True)
    print(f"🌐 Connected to {len(bot.guilds)} server(s):", flush=True)
    for guild in bot.guilds:
        print(f"   - {guild.name} (ID: {guild.id}) - {guild.member_count} members", flush=True)
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            perms = ch.permissions_for(guild.me)
            print(f"      ✅ Found #{ch.name} | View:{perms.view_channel} Send:{perms.send_messages} Embed:{perms.embed_links}", flush=True)
        else:
            print(f"      ❌ Channel {NOTIFICATION_CHANNEL_ID} not in this guild", flush=True)
    print("="*50 + "\n", flush=True)

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="WHITE_WOLF GLOBAL 🐺"))

    # Send startup message
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        embed = discord.Embed(
            title="🟢 WHITE_WOLF Bot Online!",
            description="✅ **Render Deploy Successful!**\nVoice notification system is active 24/7 🐺",
            color=discord.Color.green()
        )
        embed.add_field(name="🌐 Web Server", value=f"Running on port {PORT}", inline=True)
        embed.add_field(name="🔔 Channel", value=channel.mention, inline=True)
        embed.add_field(name="⚡ Status", value="Ready to log voice events", inline=False)
        embed.set_footer(text="WHITE_WOLF GLOBAL • Made with Joy")
        
        await channel.send(embed=embed)
        print("✅ Startup message sent!", flush=True)
    except discord.Forbidden:
        print(f"❌ FORBIDDEN: No permission in channel {NOTIFICATION_CHANNEL_ID}", flush=True)
    except discord.NotFound:
        print(f"❌ NOT FOUND: Channel {NOTIFICATION_CHANNEL_ID} doesn't exist!", flush=True)
    except Exception as e:
        print(f"❌ Startup message failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    # Debug log
    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel} | Guild: {member.guild.name}", flush=True)

    # Find notification channel
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
        print(f"❌ Channel ID {NOTIFICATION_CHANNEL_ID} not found", flush=True)
        return

    # Safe avatar
    try:
        avatar = member.display_avatar.url
    except:
        avatar = None

    try:
        if before.channel is None and after.channel is not None:
            # JOINED
            embed = discord.Embed(
                title="🎙️ Voice Joined",
                description=f"**{member.display_name}** joined voice!",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Member", value=member.mention, inline=True)
            embed.add_field(name="🔊 Channel", value=after.channel.mention, inline=True)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL")
            await channel.send(embed=embed)
            print(f"   -> ✅ JOIN sent to #{channel.name}", flush=True)

        elif before.channel is not None and after.channel is None:
            # LEFT
            embed = discord.Embed(
                title="👋 Voice Left",
                description=f"**{member.display_name}** left voice!",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Member", value=member.mention, inline=True)
            embed.add_field(name="🔊 Channel", value=before.channel.mention, inline=True)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL")
            await channel.send(embed=embed)
            print(f"   -> ✅ LEAVE sent", flush=True)

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            # MOVED
            embed = discord.Embed(
                title="🔄 Voice Moved",
                description=f"**{member.display_name}** switched channel!",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Member", value=member.mention, inline=False)
            embed.add_field(name="⬅️ From", value=before.channel.mention, inline=True)
            embed.add_field(name="➡️ To", value=after.channel.mention, inline=True)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL")
            await channel.send(embed=embed)
            print(f"   -> ✅ MOVE sent", flush=True)

    except discord.Forbidden:
        print(f"❌ No permission to send in #{channel.name}", flush=True)
    except Exception as e:
        print(f"❌ Voice event error: {e}", flush=True)
        import traceback
        traceback.print_exc()

# ========== COMMANDS ==========
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms | 🟢 Online & Ready")

@bot.command(name="test")
async def test_cmd(ctx):
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        await ctx.send(f"Testing... Sending to {channel.mention}")
        
        embed = discord.Embed(
            title="✅ Test Successful!",
            description=f"Test by {ctx.author.mention}\nChannel ID is correct!",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="ID", value=f"`{NOTIFICATION_CHANNEL_ID}`", inline=True)
        
        await channel.send(embed=embed)
        await ctx.send(f"✅ Check {channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed: {e}")

@bot.command(name="debug")
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    perms = ctx.channel.permissions_for(ctx.guild.me)
    msg = f"""
**🔍 DEBUG INFO**
**Guild:** {ctx.guild.name} (`{ctx.guild.id}`)
**This Channel:** {ctx.channel.mention} (`{ctx.channel.id}`)
**ENV Channel ID:** `{NOTIFICATION_CHANNEL_ID}`
**Found in guild?** {ch.name if ch else '❌ NOT FOUND'}
**My Perms here:** View={perms.view_channel} Send={perms.send_messages} Embed={perms.embed_links}
**Bot Latency:** {round(bot.latency*1000)}ms
**Guilds:** {len(bot.guilds)}
"""
    await ctx.send(msg)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 WHITE_WOLF Bot Commands", color=discord.Color.gold())
    embed.add_field(name="!ping", value="Check if bot is alive", inline=True)
    embed.add_field(name="!test", value="Test notification channel", inline=True)
    embed.add_field(name="!debug", value="Show debug info", inline=True)
    embed.add_field(name="Voice Logging", value="Auto logs join/leave/move", inline=False)
    embed.set_footer(text="WHITE_WOLF GLOBAL")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# ========== MAIN (Render Safe) ==========
async def main():
    # 1. Start web server FIRST - Render needs port open within 60s
    runner = await start_web_server()
    
    # 2. Start Discord bot
    try:
        async with bot:
            print("🚀 Starting Discord bot...", flush=True)
            await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Bot crashed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user", flush=True)
