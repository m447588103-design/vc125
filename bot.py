import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID = os.getenv('NOTIFICATION_CHANNELS') or os.getenv('NOTIFICATION_CHANNEL_ID')

# Parse channel ID - support multi-server JSON or single ID
CHANNEL_MAP = {}
SINGLE_ID = None
if NOTIFICATION_CHANNEL_ID:
    raw = NOTIFICATION_CHANNEL_ID.strip()
    try:
        if raw.startswith('{'):
            import json
            data = json.loads(raw)
            CHANNEL_MAP = {int(k): int(v) for k, v in data.items()}
        elif ':' in raw:
            # guild:channel format
            m = {}
            for pair in raw.split(','):
                if ':' in pair:
                    gid, cid = pair.split(':', 1)
                    m[int(gid.strip())] = int(cid.strip())
            if m:
                CHANNEL_MAP = m
            else:
                SINGLE_ID = int(raw.split(':')[-1].strip())
        else:
            SINGLE_ID = int(raw.split(',')[0].strip())
    except:
        try:
            SINGLE_ID = int(raw.split(',')[0].strip())
        except:
            pass

if not TOKEN:
    raise ValueError('DISCORD_TOKEN missing!')
if not CHANNEL_MAP and not SINGLE_ID:
    raise ValueError('Set NOTIFICATION_CHANNELS or NOTIFICATION_CHANNEL_ID')

PORT = int(os.getenv('PORT', 10000))

# Render web server - 100% working, no deps
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK - Bot Running')
    def log_message(self, format, *args):
        return

def start_web():
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"WEB LISTENING on 0.0.0.0:{PORT}", flush=True)
    httpd.serve_forever()

threading.Thread(target=start_web, daemon=True).start()
time.sleep(1)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'BOT ONLINE {bot.user} | Guilds: {len(bot.guilds)}', flush=True)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL'))

def get_channel_id(guild):
    if guild.id in CHANNEL_MAP:
        return CHANNEL_MAP[guild.id]
    return SINGLE_ID

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    cid = get_channel_id(member.guild)
    if not cid:
        return
    
    channel = member.guild.get_channel(cid) or bot.get_channel(cid)
    if not channel:
        try:
            channel = await bot.fetch_channel(cid)
        except:
            return
    
    try:
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(title='🎙️ Voice Joined', description=f'**{member.display_name}** joined **{after.channel.name}**', color=discord.Color.green())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=after.channel.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(title='👋 Voice Left', description=f'**{member.display_name}** left **{before.channel.name}**', color=discord.Color.red())
            embed.add_field(name='Member', value=member.mention, inline=True)
            embed.add_field(name='Channel', value=before.channel.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            embed = discord.Embed(title='🔄 Voice Moved', description=f'**{member.display_name}** moved {before.channel.name} -> {after.channel.name}', color=discord.Color.blue())
            await channel.send(embed=embed)
    except Exception as e:
        print(f'Error: {e}', flush=True)

bot.run(TOKEN)
