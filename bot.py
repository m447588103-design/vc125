import os
import threading
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask

# Load .env for local dev, Render uses dashboard env vars
load_dotenv()

# --- Config ---
TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNEL_ID')
PORT = int(os.getenv('PORT', 10000))

# Validate env early with friendly message
if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN is missing! Render Dashboard > Environment e add koro.')

try:
    NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID) if NOTIFICATION_CHANNEL_ID else 0
except ValueError:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID must be a number (Text Channel ID)')

if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID is missing! Render Dashboard e add koro.')

# --- Flask Keep-Alive Server for Render Web Service (Free Tier) ---
# Render Web Service free te 15 min por sleep hoye jay, kintu health check endpoint thakle
# UptimeRobot diye ping korle 24/7 online thakbe. Background Worker e eta lagbe na but thakle khoti nai.
app = Flask(__name__)

@app.route('/')
def home():
    return "🐺 WHITE_WOLF Voice Bot is Alive! ✅", 200

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    # Render er jonno 0.0.0.0 te bind kora must
    app.run(host='0.0.0.0', port=PORT, debug=False)

# Start Flask in background thread (daemon)
threading.Thread(target=run_flask, daemon=True).start()
print(f"🌐 Keep-alive server started on port {PORT}")

# --- Discord Bot Setup ---
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # IMPORTANT: Discord Developer Portal e Server Members Intent ON koro
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print('===================================')
    print('🐺 WHITE_WOLF Voice Bot Online')
    print(f'🤖 Logged in as: {bot.user} (ID: {bot.user.id})')
    print(f'🌐 Servers: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'   - {guild.name} ({guild.id})')
    print('===================================')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    # Notification channel fetch with fallback
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(NOTIFICATION_CHANNEL_ID)
        except Exception as e:
            print(f'❌ Notification channel not found! ID: {NOTIFICATION_CHANNEL_ID} Error: {e}')
            return

    try:
        if before.channel is None and after.channel is not None:
            # Joined
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

        elif before.channel is not None and after.channel is None:
            # Left
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

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            # Moved
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

    except Exception as e:
        print(f"⚠️ Error in on_voice_state_update: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}")
    import traceback
    traceback.print_exc()

# --- Run ---
if __name__ == "__main__":
    print("🚀 Starting bot...")
    bot.run(TOKEN, log_handler=None)
