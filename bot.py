"""
🐺 WHITE_WOLF Voice Notification Bot - KITT Style
Kew voice e join korle naam dhore bolbe, leave nile bolbe
Render 100% compatible - aiohttp version
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from aiohttp import web

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

print(f"🔧 CONFIG: TOKEN={bool(TOKEN)} | CHANNEL={CHANNEL_ID_RAW} | PORT={PORT}", flush=True)

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN missing!")
try:
    NOTIFICATION_CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else 0
except:
    raise ValueError(f"❌ CHANNEL_ID must be number, got: {CHANNEL_ID_RAW}")
if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError("❌ NOTIFICATION_CHANNEL_ID missing!")

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ========== WEB SERVER FOR RENDER ==========
async def health_handler(request):
    return web.Response(text="OK - WHITE_WOLF Bot Running", status=200)

async def home_handler(request):
    return web.Response(text="WHITE_WOLF Voice Bot Alive! KITT Style Bot Ready", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', home_handler)
    app.router.add_get('/health', health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✅ WEB SERVER started on 0.0.0.0:{PORT}", flush=True)
    return runner

# ========== BOT READY ==========
@bot.event
async def on_ready():
    print("\n" + "="*50, flush=True)
    print("🐺 WHITE_WOLF KITT BOT ONLINE!", flush=True)
    print(f"🤖 {bot.user} | Guilds: {len(bot.guilds)}", flush=True)
    print(f"🔔 Notification Channel ID: {NOTIFICATION_CHANNEL_ID}", flush=True)
    for guild in bot.guilds:
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f"   ✅ Found #{ch.name} in {guild.name}", flush=True)
    print("="*50 + "\n", flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="WHITE_WOLF GLOBAL 🐺"))

    # Startup message - KITT style
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        embed = discord.Embed(
            title="🟢 WHITE_WOLF KITT Bot Online!",
            description="✅ Bot ready! Kew voice e join/leave korle ami naam dhore bole dibo 🐺",
            color=discord.Color.green()
        )
        embed.add_field(name="🎙️ Join", value="Kew join korle bolbo", inline=True)
        embed.add_field(name="👋 Leave", value="Kew leave nile bolbo", inline=True)
        embed.add_field(name="🔄 Move", value="Channel change korle bolbo", inline=True)
        embed.set_footer(text="WHITE_WOLF GLOBAL • KITT Style")
        await channel.send(embed=embed)
        print("✅ Startup KITT message sent!", flush=True)
    except Exception as e:
        print(f"❌ Startup failed: {e}", flush=True)

# ========== MAIN VOICE LOGIC - KITT STYLE ==========
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    print(f"[VOICE] {member.display_name} | {before.channel} -> {after.channel}", flush=True)

    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        except:
            return

    try:
        avatar = member.display_avatar.url if member.display_avatar else None
    except:
        avatar = None

    try:
        # === JOIN ===
        if before.channel is None and after.channel is not None:
            # KITT style Bangla + English mix
            embed = discord.Embed(
                title="🎙️ Voice e Join Korse!",
                description=f"**{member.display_name}** voice channel e **join korse**!",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Member", value=f"{member.mention}\n`{member.display_name}`", inline=True)
            embed.add_field(name="🔊 Channel", value=f"{after.channel.mention}\n`{after.channel.name}`", inline=True)
            embed.add_field(name="📢 Message", value=f"**{member.display_name}** joined **{after.channel.name}**", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL • KITT Bot")
            await channel.send(embed=embed)
            print(f"   -> JOIN: {member.display_name} -> {after.channel.name}", flush=True)

        # === LEAVE ===
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="👋 Voice Theke Leave Nise!",
                description=f"**{member.display_name}** voice theke **leave nise**!",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Member", value=f"{member.mention}\n`{member.display_name}`", inline=True)
            embed.add_field(name="🔊 Channel", value=f"{before.channel.mention}\n`{before.channel.name}`", inline=True)
            embed.add_field(name="📢 Message", value=f"**{member.display_name}** left **{before.channel.name}**", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL • KITT Bot")
            await channel.send(embed=embed)
            print(f"   -> LEAVE: {member.display_name} <- {before.channel.name}", flush=True)

        # === MOVE ===
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            embed = discord.Embed(
                title="🔄 Voice Channel Change Korse!",
                description=f"**{member.display_name}** channel change korse!",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Member", value=member.mention, inline=False)
            embed.add_field(name="⬅️ From", value=f"{before.channel.mention}\n`{before.channel.name}`", inline=True)
            embed.add_field(name="➡️ To", value=f"{after.channel.mention}\n`{after.channel.name}`", inline=True)
            embed.add_field(name="📢 Message", value=f"**{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**", inline=False)
            if avatar:
                embed.set_thumbnail(url=avatar)
            embed.set_footer(text="🐺 WHITE_WOLF GLOBAL • KITT Bot")
            await channel.send(embed=embed)
            print(f"   -> MOVE: {member.display_name} {before.channel.name} -> {after.channel.name}", flush=True)

    except Exception as e:
        print(f"❌ Voice error: {e}", flush=True)

# ========== COMMANDS (Agher thekei ache) ==========
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms | KITT Bot Online 🐺")

@bot.command(name="test")
async def test_cmd(ctx):
    """Test korbe notification channel thik ache kina"""
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        await ctx.send(f"🔍 Testing... {channel.mention} e pathacchi")
        
        # Join er moto test
        embed = discord.Embed(
            title="🎙️ Voice e Join Korse! (TEST)",
            description=f"**{ctx.author.display_name}** voice channel e **join korse**! (Test)",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Member", value=ctx.author.mention, inline=True)
        embed.add_field(name="🔊 Channel", value="Test Channel", inline=True)
        embed.add_field(name="📢 Message", value=f"**{ctx.author.display_name}** joined Test", inline=False)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Test done! Check {channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed: {e}")

@bot.command(name="debug")
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    perms = ctx.channel.permissions_for(ctx.guild.me)
    await ctx.send(f"""
**🔍 KITT Bot Debug**
Guild: {ctx.guild.name} ({ctx.guild.id})
Notification Channel: {ch.name if ch else 'NOT FOUND'} ({NOTIFICATION_CHANNEL_ID})
Perms: View={perms.view_channel} Send={perms.send_messages} Embed={perms.embed_links}
Latency: {round(bot.latency*1000)}ms
""")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🐺 WHITE_WOLF KITT Bot - Help", description="KITT style voice notification bot", color=discord.Color.gold())
    embed.add_field(name="🎙️ Auto Features", value="• Join korle naam dhore bolbe\n• Leave nile bolbe\n• Move korle bolbe", inline=False)
    embed.add_field(name="💬 Commands", value="`!ping` - Bot alive?\n`!test` - Test notification\n`!debug` - Debug info\n`!help` - Ei help", inline=False)
    embed.set_footer(text="WHITE_WOLF GLOBAL")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# ========== MAIN ==========
async def main():
    runner = await start_web_server()
    try:
        async with bot:
            print("🚀 Starting KITT Bot...", flush=True)
            await bot.start(TOKEN)
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
