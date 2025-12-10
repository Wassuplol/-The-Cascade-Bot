"""
General fun commands cog for The Cascade Bot.

This module implements fun commands like ping, serverinfo, and other
entertainment features for users.
"""

import discord
from discord.ext import commands
import random
import time
from datetime import datetime
from core.utils import create_embed, format_timedelta, time_since
from core.logger import BotLogger


class GeneralFun(commands.Cog):
    """
    General fun commands cog implementing ping, serverinfo, and other commands.
    """
    
    def __init__(self, bot):
        """
        Initialize the general fun cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = BotLogger(__name__)
    
    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context):
        """
        Check the bot's latency and respond with ping information.
        
        Args:
            ctx (commands.Context): Command context
        """
        # Calculate the round-trip time
        start_time = time.time()
        message = await ctx.send("Pong! 🏓")
        end_time = time.time()
        
        # Calculate API and message round-trip times
        api_ping = self.bot.latency * 1000  # Convert to milliseconds
        message_ping = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Create embed with ping information
        embed = create_embed(
            title="🏓 Pong!",
            description="Here's the bot's connection information:",
            fields=[
                {"name": "API Latency", "value": f"{api_ping:.2f}ms", "inline": True},
                {"name": "Message Latency", "value": f"{message_ping:.2f}ms", "inline": True},
                {"name": "Status", "value": "🟢 Online", "inline": True}
            ],
            color=discord.Color.green()
        )
        
        await message.edit(content="", embed=embed)
    
    @commands.command(name='serverinfo', aliases=['guildinfo', 'si'])
    async def serverinfo(self, ctx: commands.Context):
        """
        Display detailed information about the server.
        
        Args:
            ctx (commands.Context): Command context
        """
        guild = ctx.guild
        
        # Calculate member counts
        total_members = guild.member_count
        humans = sum(1 for member in guild.members if not member.bot)
        bots = total_members - humans
        
        # Get creation date info
        created_at = guild.created_at
        age = datetime.utcnow() - created_at
        
        # Get boost information
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        boosters = sum(1 for member in guild.members if member.premium_since)
        
        # Get role and channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles) - 1  # Subtract 1 for @everyone
        
        # Get owner info
        owner = guild.owner
        if not owner:
            # Fallback if owner is not cached
            owner = await self.bot.fetch_user(guild.owner_id)
        
        # Create embed with server information
        embed = create_embed(
            title=f"🏛️ {guild.name}",
            description=f"Information about {guild.name}",
            fields=[
                {"name": "Owner", "value": f"{owner} ({owner.mention})", "inline": True},
                {"name": "Created", "value": f"{created_at.strftime('%B %d, %Y')} ({time_since(created_at)})", "inline": True},
                {"name": "Age", "value": format_timedelta(age), "inline": True},
                {"name": "Members", "value": f"👥 {total_members} (Humans: {humans}, Bots: {bots})", "inline": True},
                {"name": "Boosts", "value": f"💎 Level {boost_level} ({boost_count} boosts, {boosters} boosters)", "inline": True},
                {"name": "Channels", "value": f"💬 {text_channels} text, 🔊 {voice_channels} voice, 📁 {categories} categories", "inline": False},
                {"name": "Roles", "value": f"🏷️ {roles} roles", "inline": True},
                {"name": "Emoji Count", "value": f"😊 {len(guild.emojis)} emojis", "inline": True},
                {"name": "Stickers", "value": f"🎨 {len(guild.stickers)} stickers", "inline": True}
            ],
            color=discord.Color.blue()
        )
        
        # Set thumbnail to guild icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['user', 'ui'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """
        Display detailed information about a user.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member, optional): Member to get info for (defaults to command author)
        """
        if member is None:
            member = ctx.author
        
        # Get creation and join dates
        created_at = member.created_at
        joined_at = member.joined_at
        created_age = datetime.utcnow() - created_at
        joined_age = datetime.utcnow() - joined_at
        
        # Get roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles.reverse()  # Put highest role first
        
        # Get status information
        status = str(member.status).title()
        if member.activities:
            activities = []
            for activity in member.activities:
                if activity.type == discord.ActivityType.playing:
                    activities.append(f"🎮 Playing {activity.name}")
                elif activity.type == discord.ActivityType.streaming:
                    activities.append(f"📺 Streaming {activity.name}")
                elif activity.type == discord.ActivityType.listening:
                    activities.append(f"🎧 Listening to {activity.name}")
                elif activity.type == discord.ActivityType.watching:
                    activities.append(f"📺 Watching {activity.name}")
                elif activity.type == discord.ActivityType.custom:
                    activities.append(f"✏️ {activity.name}")
            status += f"\n{', '.join(activities)}"
        
        # Create embed with user information
        embed = create_embed(
            title=f"👤 {member.display_name}",
            fields=[
                {"name": "Username", "value": str(member), "inline": True},
                {"name": "Account Created", "value": f"{created_at.strftime('%B %d, %Y')} ({time_since(created_at)})", "inline": True},
                {"name": "Account Age", "value": format_timedelta(created_age), "inline": True},
                {"name": "Joined Server", "value": f"{joined_at.strftime('%B %d, %Y')} ({time_since(joined_at)})", "inline": True},
                {"name": "Join Age", "value": format_timedelta(joined_age), "inline": True},
                {"name": "Status", "value": status, "inline": False},
                {"name": f"Roles ({len(roles)})", "value": ", ".join(roles) or "No roles", "inline": False}
            ],
            color=member.color if member.color.value != 0 else discord.Color.blue()
        )
        
        # Set thumbnail to user avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roll')
    async def roll(self, ctx: commands.Context, dice: str = "1d6"):
        """
        Roll virtual dice in NdN format.
        
        Args:
            ctx (commands.Context): Command context
            dice (str): Dice format (e.g., 2d6, 1d20, d100)
        """
        try:
            # Parse the dice string
            if 'd' not in dice:
                await ctx.send("Please use NdN format (e.g., 2d6, 1d20)")
                return
            
            parts = dice.lower().split('d')
            if len(parts) != 2:
                await ctx.send("Please use NdN format (e.g., 2d6, 1d20)")
                return
            
            if parts[0] == '':
                num_dice = 1
            else:
                num_dice = int(parts[0])
            
            num_sides = int(parts[1])
            
            # Validate inputs
            if num_dice <= 0 or num_dice > 100:
                await ctx.send("Number of dice must be between 1 and 100")
                return
            
            if num_sides <= 0 or num_sides > 1000:
                await ctx.send("Number of sides must be between 1 and 1000")
                return
            
            # Roll the dice
            results = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(results)
            
            # Create embed with results
            if num_dice == 1:
                embed = create_embed(
                    title=f"🎲 You rolled {dice}",
                    description=f"You rolled: **{results[0]}**",
                    color=discord.Color.gold()
                )
            else:
                embed = create_embed(
                    title=f"🎲 You rolled {dice}",
                    description=f"Individual rolls: **{', '.join(map(str, results))}**\nTotal: **{total}**",
                    color=discord.Color.gold()
                )
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("Please use NdN format (e.g., 2d6, 1d20)")
        except Exception as e:
            self.logger.error(f"Error rolling dice: {e}", exc_info=True)
            await ctx.send("An error occurred while rolling the dice.")
    
    @commands.command(name='choose', aliases=['choice', 'pick'])
    async def choose(self, ctx: commands.Context, *choices: str):
        """
        Have the bot choose randomly from provided options.
        
        Args:
            ctx (commands.Context): Command context
            *choices (str): Options to choose from
        """
        if len(choices) < 2:
            await ctx.send("Please provide at least 2 options to choose from!")
            return
        
        # Randomly select a choice
        chosen = random.choice(choices)
        
        # Create embed with result
        embed = create_embed(
            title="🔮 I have chosen...",
            description=f"My choice is: **{chosen}**",
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coinflip', aliases=['flip', 'coin'])
    async def coinflip(self, ctx: commands.Context):
        """
        Flip a coin and get heads or tails.
        
        Args:
            ctx (commands.Context): Command context
        """
        result = random.choice(["Heads", "Tails"])
        
        # Create embed with result
        embed = create_embed(
            title="🪙 Coin Flip",
            description=f"It's **{result}**!",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='avatar', aliases=['pfp'])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """
        Get a user's avatar.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member, optional): Member to get avatar for (defaults to command author)
        """
        if member is None:
            member = ctx.author
        
        # Create embed with avatar
        embed = create_embed(
            title=f"{member.display_name}'s Avatar",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(
            name="Links",
            value=f"[PNG]({member.display_avatar.replace(format='png', size=1024).url}) | "
                  f"[JPG]({member.display_avatar.replace(format='jpg', size=1024).url}) | "
                  f"[WEBP]({member.display_avatar.replace(format='webp', size=1024).url})",
            inline=False
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    """
    Set up the general fun cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(GeneralFun(bot))