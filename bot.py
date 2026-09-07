import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID', '0'))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('===================================')
    print('🐺 WHITE_WOLF Voice Bot Online')
    print(f'🤖 Logged in as: {bot.user}')
    print(f'🌐 Servers: {len(bot.guilds)}')
    print('===================================')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='WHITE_WOLF GLOBAL 🐺'))

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    channel = member.guild.get_channel(NOTIFICATION_CHANNEL_ID)
    if channel is None:
        print('❌ Notification channel not found!')
        return

    if before.channel is None and after.channel is not None:
        embed = discord.Embed(title='🎙️ Voice Channel Joined', description=f'**{member.display_name}** just joined the voice channel!', color=discord.Color.green())
        embed.add_field(name='👤 Member', value=member.mention, inline=True)
        embed.add_field(name='🔊 Channel', value=after.channel.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
        await channel.send(embed=embed)

    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(title='👋 Voice Channel Left', description=f'**{member.display_name}** left the voice channel.', color=discord.Color.red())
        embed.add_field(name='👤 Member', value=member.mention, inline=True)
        embed.add_field(name='🔊 Channel', value=before.channel.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
        await channel.send(embed=embed)

    elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        embed = discord.Embed(title='🔄 Voice Channel Moved', description=f'**{member.display_name}** moved to another voice channel.', color=discord.Color.blue())
        embed.add_field(name='👤 Member', value=member.mention, inline=False)
        embed.add_field(name='⬅️ From', value=before.channel.mention, inline=True)
        embed.add_field(name='➡️ To', value=after.channel.mention, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text='🐺 WHITE_WOLF GLOBAL • ⚡ Made with Joy')
        await channel.send(embed=embed)

if not TOKEN:
    raise ValueError('❌ DISCORD_TOKEN is missing!')
if NOTIFICATION_CHANNEL_ID == 0:
    raise ValueError('❌ NOTIFICATION_CHANNEL_ID is missing!')

bot.run(TOKEN)
