import os
import threading
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID_RAW = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN missing! Render Dashboard > Environment e add koro.')

try:
    NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID_RAW) if NOTIFICATION_CHANNEL_ID_RAW else 0
except ValueError:
    raise ValueError(f'❌ NOTIFICATION_CHANNEL_ID must be number, got: {NOTIFICATION_CHANNEL_ID_RAW}')

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID missing!')

# --- Flask Keep-Alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🐺 WHITE_WOLF Voice Bot is Alive! ✅", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    # use_reloader=False important, naile Render e 2 bar start hoy
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()
print(f"🌐 Keep-alive server started on port {PORT}")

# --- Discord ---
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # Portal e ON korte hobe
intents.voice_states = True
intents.message_content = True  # !test command er jonno

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('===================================')
    print('🐺 WHITE_WOLF Voice Bot Online')
    print(f'🤖 Logged in as: {bot.user} (ID: {bot.user.id})')
    print(f'🔔 Notification Channel ID: {NOTIFICATION_CHANNEL_ID}')
    print(f'🌐 Servers: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'   - {guild.name} ({guild.id})')
        # Check if notification channel exists in this guild
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f'      ✅ Found notification channel in this guild: #{ch.name}')
        # List all text channels for debugging
        text_channels = [f"{c.name} ({c.id})" for c in guild.text_channels[:10]]
        print(f'      Text channels: {", ".join(text_channels)}')

    print('===================================')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

    # Try to send online message on startup to confirm permissions
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        if channel:
            print(f"✅ Notification channel found: #{channel.name} in {channel.guild.name}")
            embed = discord.Embed(
                title='🟢 Bot Online',
                description='Voice notification system is now active! 🐺',
                color=discord.Color.gold()
            )
            embed.set_footer(text='If you see this, notification channel is correct ✅')
            await channel.send(embed=embed)
            print("✅ Startup test message sent!")
        else:
            print(f"❌ Could not find notification channel ID: {NOTIFICATION_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Failed to send startup message: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='ping')
async def ping_cmd(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency*1000)}ms | Bot is alive 🐺')

@bot.command(name='test')
async def test_cmd(ctx):
    """Notification channel e test embed pathabe"""
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        embed = discord.Embed(
            title='✅ Test Notification',
            description=f'Test triggered by {ctx.author.mention}\nIf you see this, channel ID is correct!',
            color=discord.Color.green()
        )
        embed.add_field(name='Channel ID', value=f'`{NOTIFICATION_CHANNEL_ID}`', inline=True)
        embed.add_field(name='Test Channel', value=channel.mention, inline=True)
        await channel.send(embed=embed)
        await ctx.send(f"✅ Test sent to {channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Test failed: {e}")
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='debug')
async def debug_cmd(ctx):
    info = f"""
**Debug Info**
Bot: {bot.user} ({bot.user.id})
Guild: {ctx.guild.name} ({ctx.guild.id})
Notification ID from ENV: `{NOTIFICATION_CHANNEL_ID}`
Current Channel: {ctx.channel.mention} ({ctx.channel.id})
Members Intent: {bot.intents.members}
Voice States Intent: {bot.intents.voice_states}
Guilds: {len(bot.guilds)}
"""
    await ctx.send(info)

@bot.event
async def on_voice_state_update(member, before, after):
    # DEBUG LOG - protibar voice state change hole log e dekhabe
    print(f"[VOICE EVENT] {member.display_name} ({member.id}) | Before: {before.channel} | After: {after.channel} | Bot? {member.bot}")

    if member.bot:
        print(f"   -> Ignored (bot)")
        return

    # Original logic er moto member.guild.get_channel use korbo (most reliable)
    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
            print(f"   -> Fetched channel via API: {channel}")
        except Exception as e:
            print(f'❌ Notification channel not found! ID: {NOTIFICATION_CHANNEL_ID} Error: {e}')
            return

    if channel is None:
        print(f"❌ Still no channel found for ID {NOTIFICATION_CHANNEL_ID} in guild {member.guild.name}")
        return

    print(f"   -> Will send notification to #{channel.name}")

    try:
        if before.channel is None and after.channel is not None:
            # JOINED
            print(f"   -> JOIN event")
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
            print(f"   -> ✅ Join notification sent")

        elif before.channel is not None and after.channel is None:
            # LEFT
            print(f"   -> LEAVE event")
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
            print(f"   -> ✅ Leave notification sent")

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            # MOVED
            print(f"   -> MOVE event {before.channel} -> {after.channel}")
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
            print(f"   -> ✅ Move notification sent")
        else:
            print(f"   -> No action (mute/deafen etc)")

    except discord.Forbidden as e:
        print(f"❌ FORBIDDEN - Bot er permission nai #{channel.name} e message pathanor! Error: {e}")
    except Exception as e:
        print(f"⚠️ Error in on_voice_state_update: {e}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting bot...")
    bot.run(TOKEN, log_handler=None)
