"""
Information utility cog for The Cascade Bot.

This module implements utility commands for getting information about
the bot, server stats, and other useful data.
"""

import discord
from discord.ext import commands
import psutil
import platform
from datetime import datetime
from core.utils import create_embed, format_timedelta
from core.logger import BotLogger


class Information(commands.Cog):
    """
    Information utility cog implementing commands for bot and server information.
    """
    
    def __init__(self, bot):
        """
        Initialize the information utility cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = BotLogger(__name__)
    
    @commands.command(name='botinfo', aliases=['info', 'bi'])
    async def botinfo(self, ctx: commands.Context):
        """
        Display information about the bot.
        
        Args:
            ctx (commands.Context): Command context
        """
        # Get bot statistics
        uptime = self.bot.get_uptime()
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        channel_count = sum(len(guild.channels) for guild in self.bot.guilds)
        
        # Get performance stats
        performance_stats = await self.bot.get_performance_stats()
        
        # Get system information
        python_version = platform.python_version()
        discord_version = discord.__version__
        
        # Get memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create embed with bot information
        embed = create_embed(
            title=f"🤖 {self.bot.user.display_name}",
            description="Information about The Cascade Bot",
            fields=[
                {"name": "Developer", "value": "The Cascade Team", "inline": True},
                {"name": "Uptime", "value": performance_stats['uptime_formatted'], "inline": True},
                {"name": "Latency", "value": performance_stats['latency'], "inline": True},
                {"name": "Servers", "value": str(guild_count), "inline": True},
                {"name": "Users", "value": f"{user_count:,}", "inline": True},
                {"name": "Channels", "value": str(channel_count), "inline": True},
                {"name": "Commands Executed", "value": str(performance_stats['commands_executed']), "inline": True},
                {"name": "Messages Processed", "value": str(performance_stats['messages_processed']), "inline": True},
                {"name": "Python Version", "value": python_version, "inline": True},
                {"name": "Discord.py Version", "value": discord_version, "inline": True},
                {"name": "Memory Usage", "value": f"{memory_usage:.2f} MB", "inline": True}
            ],
            color=discord.Color.blue()
        )
        
        # Set thumbnail to bot avatar
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='stats', aliases=['stat', 'top'])
    async def stats(self, ctx: commands.Context):
        """
        Display detailed statistics about the bot's performance.
        
        Args:
            ctx (commands.Context): Command context
        """
        # Get bot statistics
        uptime = self.bot.get_uptime()
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)
        channel_count = sum(len(guild.channels) for guild in self.bot.guilds)
        
        # Get performance stats
        performance_stats = await self.bot.get_performance_stats()
        
        # Get system information
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent()
        
        # Calculate approximate daily usage
        hours_up = uptime / 3600
        commands_per_hour = performance_stats['commands_executed'] / max(hours_up, 1)
        messages_per_hour = performance_stats['messages_processed'] / max(hours_up, 1)
        
        # Create embed with detailed stats
        embed = create_embed(
            title="📊 Bot Statistics",
            fields=[
                {"name": "Performance", "value": "📊", "inline": False},
                {"name": "Uptime", "value": performance_stats['uptime_formatted'], "inline": True},
                {"name": "Commands Executed", "value": f"{performance_stats['commands_executed']:,}", "inline": True},
                {"name": "Messages Processed", "value": f"{performance_stats['messages_processed']:,}", "inline": True},
                {"name": "Avg. Commands/Hour", "value": f"{commands_per_hour:.1f}", "inline": True},
                {"name": "Avg. Messages/Hour", "value": f"{messages_per_hour:.1f}", "inline": True},
                {"name": "System", "value": "🖥️", "inline": False},
                {"name": "Memory Usage", "value": f"{memory_usage:.2f} MB", "inline": True},
                {"name": "CPU Usage", "value": f"{cpu_percent}%", "inline": True},
                {"name": "Latency", "value": performance_stats['latency'], "inline": True},
                {"name": "Server Count", "value": str(guild_count), "inline": True},
                {"name": "User Count", "value": f"{user_count:,}", "inline": True},
                {"name": "Channel Count", "value": str(channel_count), "inline": True}
            ],
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx: commands.Context, *, command: str = None):
        """
        Display help information for commands.
        
        Args:
            ctx (commands.Context): Command context
            command (str, optional): Specific command to get help for
        """
        if command:
            # Show help for a specific command
            cmd = self.bot.get_command(command)
            if cmd is None:
                await ctx.send(f"Command `{command}` not found.")
                return
            
            # Build help embed for specific command
            embed = create_embed(
                title=f"❓ Help: {cmd.qualified_name}",
                description=cmd.help or "No description available.",
                color=discord.Color.blue()
            )
            
            # Add usage information
            signature = f"{ctx.prefix}{cmd.qualified_name}"
            if cmd.signature:
                signature += f" {cmd.signature}"
            embed.add_field(name="Usage", value=f"`{signature}`", inline=False)
            
            # Add aliases if they exist
            if cmd.aliases:
                aliases_str = ", ".join([f"`{alias}`" for alias in cmd.aliases])
                embed.add_field(name="Aliases", value=aliases_str, inline=False)
            
            await ctx.send(embed=embed)
        else:
            # Show general help with command categories
            embed = create_embed(
                title="❓ The Cascade Bot Help",
                description="Here are the available command categories:",
                color=discord.Color.blue()
            )
            
            # Group commands by cog
            cogs = {}
            for cmd in self.bot.commands:
                if cmd.cog is None:
                    continue
                cog_name = cmd.cog.qualified_name
                if cog_name not in cogs:
                    cogs[cog_name] = []
                cogs[cog_name].append(cmd)
            
            # Add fields for each cog
            for cog_name, commands_list in cogs.items():
                # Limit to 5 commands per category to avoid embed size issues
                cmd_list = [f"`{cmd.name}`" for cmd in commands_list[:5]]
                if len(commands_list) > 5:
                    cmd_list.append(f"... and {len(commands_list) - 5} more")
                
                embed.add_field(
                    name=cog_name,
                    value=", ".join(cmd_list),
                    inline=False
                )
            
            # Add footer with more information
            embed.set_footer(text=f"Use {ctx.prefix}help <command> for more info on a specific command")
            
            await ctx.send(embed=embed)


async def setup(bot):
    """
    Set up the information utility cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(Information(bot))