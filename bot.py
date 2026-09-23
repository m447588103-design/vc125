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

print(f"🔧 ENV CHECK: TOKEN exists? {bool(TOKEN)} | CHANNEL_ID raw: {NOTIFICATION_CHANNEL_ID_RAW} | PORT: {PORT}")

if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN missing!')

try:
    NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID_RAW) if NOTIFICATION_CHANNEL_ID_RAW else 0
except ValueError:
    raise ValueError(f'❌ NOTIFICATION_CHANNEL_ID must be number, got: {NOTIFICATION_CHANNEL_ID_RAW}')

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID missing!')

# --- Flask Keep-Alive (Render Web Service) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🐺 WHITE_WOLF Voice Bot is Alive! ✅", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    try:
        print(f"🌐 Starting Flask on 0.0.0.0:{PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Flask failed: {e}")

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
print(f"🌐 Keep-alive thread started")

# --- Discord ---
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('===================================')
    print('🐺 WHITE_WOLF Voice Bot Online')
    print(f'🤖 {bot.user} (ID: {bot.user.id})')
    print(f'🔔 Target Channel ID: {NOTIFICATION_CHANNEL_ID}')
    print(f'🌐 Guilds: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'   - {guild.name} ({guild.id}) | Members: {guild.member_count}')
        # Try to find notification channel
        ch = guild.get_channel(NOTIFICATION_CHANNEL_ID)
        if ch:
            print(f'      ✅ FOUND notification channel here: #{ch.name} ({ch.id}) Type: {ch.type}')
            # Check permissions
            perms = ch.permissions_for(guild.me)
            print(f'      Permissions: View={perms.view_channel} Send={perms.send_messages} Embed={perms.embed_links}')
        else:
            print(f'      ❌ Channel {NOTIFICATION_CHANNEL_ID} NOT in this guild')

    print('===================================')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

    # STARTUP TEST
    print("📨 Trying to send startup message...")
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            print("   -> get_channel returned None, trying fetch_channel...")
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        print(f"   -> Channel object: {channel} | Guild: {channel.guild.name if hasattr(channel, 'guild') else 'N/A'}")
        
        # Try plain text first (embed permission er jonno fail hote pare)
        await channel.send("🟢 **WHITE_WOLF Bot Online!** Voice log active. Jodi eta dekho tahole channel thik ache ✅")
        print("✅ Startup plain text sent!")
        
        embed = discord.Embed(
            title='🟢 Bot Online - Embed Test',
            description='Voice notification system active! 🐺\nEmbed kaj korle eta dekhba.',
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)
        print("✅ Startup embed sent!")
        
    except discord.Forbidden as e:
        print(f"❌ FORBIDDEN: Bot er permission nai! {e}")
        print("   -> Channel Settings > Permissions > Bot ke View, Send Messages, Embed Links dao")
    except discord.NotFound as e:
        print(f"❌ NOT FOUND: Channel ID vul! {e}")
        print(f"   -> {NOTIFICATION_CHANNEL_ID} ei ID er channel exist kore na ba bot oi server e nai")
    except Exception as e:
        print(f"❌ Failed to send startup message: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='ping')
async def ping_cmd(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency*1000)}ms')

@bot.command(name='test')
async def test_cmd(ctx):
    print(f"[CMD] !test by {ctx.author} in #{ctx.channel.name}")
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        
        await ctx.send(f"🔍 Trying to send to {channel.mention} ({channel.id}) in {channel.guild.name}...")
        await channel.send(f"✅ Test from {ctx.author.mention} - Plain text works!")
        
        embed = discord.Embed(title='✅ Test Embed', description=f'Triggered by {ctx.author.mention}', color=discord.Color.green())
        await channel.send(embed=embed)
        await ctx.send(f"✅ Sent to {channel.mention}")
        print("✅ !test success")
    except Exception as e:
        await ctx.send(f"❌ Test failed: {e}")
        print(f"❌ !test failed: {e}")
        import traceback
        traceback.print_exc()

@bot.command(name='debug')
async def debug_cmd(ctx):
    ch = ctx.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    bot_ch = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    info = f"""
**DEBUG**
Guild: {ctx.guild.name} ({ctx.guild.id})
This Channel: {ctx.channel.name} ({ctx.channel.id})
ENV Channel ID: `{NOTIFICATION_CHANNEL_ID}`
guild.get_channel: {ch} ({ch.name if ch else 'None'})
bot.get_channel: {bot_ch} ({bot_ch.name if bot_ch else 'None'})
Bot perms in this channel: View={ctx.channel.permissions_for(ctx.guild.me).view_channel} Send={ctx.channel.permissions_for(ctx.guild.me).send_messages} Embed={ctx.channel.permissions_for(ctx.guild.me).embed_links}
Intents: members={bot.intents.members} voice_states={bot.intents.voice_states} message_content={bot.intents.message_content}
"""
    await ctx.send(info)
    print(info)

@bot.event
async def on_voice_state_update(member, before, after):
    print(f"\n[VOICE] {member.display_name} ({member.id}) | {before.channel} -> {after.channel} | bot={member.bot} | guild={member.guild.name}")

    if member.bot:
        print("   -> Skip bot")
        return

    # Find notification channel - try guild first
    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    source = "guild.get_channel"
    if channel is None:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        source = "bot.get_channel"
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
            source = "fetch_channel"
        except Exception as e:
            print(f"❌ Channel fetch failed: {e}")
            return

    if channel is None:
        print(f"❌ No channel for ID {NOTIFICATION_CHANNEL_ID}")
        return

    print(f"   -> Target: #{channel.name} via {source} | Guild: {channel.guild.name}")

    # Avatar safe
    try:
        avatar_url = member.display_avatar.url
    except:
        avatar_url = None

    try:
        if before.channel is None and after.channel is not None:
            print("   -> EVENT: JOIN")
            embed = discord.Embed(title='🎙️ Voice Joined', description=f'**{member.display_name}** joined {after.channel.mention}', color=discord.Color.green())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=after.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            await channel.send(embed=embed)
            print("   -> ✅ Sent")

        elif before.channel is not None and after.channel is None:
            print("   -> EVENT: LEAVE")
            embed = discord.Embed(title='👋 Voice Left', description=f'**{member.display_name}** left {before.channel.mention}', color=discord.Color.red())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=before.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            await channel.send(embed=embed)
            print("   -> ✅ Sent")

        elif before.channel and after.channel and before.channel.id != after.channel.id:
            print(f"   -> EVENT: MOVE {before.channel.name} -> {after.channel.name}")
            embed = discord.Embed(title='🔄 Voice Moved', description=f'**{member.display_name}** moved', color=discord.Color.blue())
            embed.add_field(name='From', value=before.channel.mention, inline=True)
            embed.add_field(name='To', value=after.channel.mention, inline=True)
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            await channel.send(embed=embed)
            print("   -> ✅ Sent")
        else:
            print("   -> Ignored (mute/deafen)")

    except discord.Forbidden as e:
        print(f"❌ FORBIDDEN in #{channel.name}: {e}")
        try:
            await channel.send(f"❌ Ami {after.channel.mention if after.channel else before.channel.mention} er log pathate parchi na, permission nai! {member.mention} joined/left.")
        except:
            pass
    except Exception as e:
        print(f"❌ Error sending: {e}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print(f"[MSG] {message.author}: {message.content} in #{message.channel.name}")
    await bot.process_commands(message)

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting bot...")
    bot.run(TOKEN, log_handler=None)
