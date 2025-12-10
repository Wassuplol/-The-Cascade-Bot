"""
Punishment system cog for The Cascade Bot.

This module implements the core punishment commands like warn, mute, kick, and ban
with proper logging and integration with the database system.
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
from core.utils import is_mod_or_admin, create_embed, parse_duration
from core.logger import BotLogger


class PunishmentSystem(commands.Cog):
    """
    Punishment system cog implementing warn, mute, kick, and ban commands.
    """
    
    def __init__(self, bot):
        """
        Initialize the punishment system cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = BotLogger(__name__)
    
    @commands.command(name='warn', aliases=['warning'])
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Warn a member for inappropriate behavior.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member): Member to warn
            reason (str): Reason for the warning
        """
        # Check if user is trying to warn themselves
        if member.id == ctx.author.id:
            await ctx.send("You cannot warn yourself.")
            return
        
        # Check if user is trying to warn the bot
        if member.id == self.bot.user.id:
            await ctx.send("I cannot warn myself.")
            return
        
        # Check hierarchy - can't moderate someone with higher/equal role
        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot warn someone with a higher or equal role.")
            return
        
        try:
            # Create a temporary embed for the user
            warn_embed = create_embed(
                title="⚠️ Warning",
                description=f"You have been warned in {ctx.guild.name}",
                fields=[
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": True}
                ],
                color=discord.Color.orange()
            )
            
            # Try to send DM to the user
            try:
                await member.send(embed=warn_embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass
            
            # Log the warning in the database
            infraction_id = await self.bot.db_manager.log_moderation_action(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                action_type="warn",
                reason=reason
            )
            
            # Update user's warning count in database
            user_data = await self.bot.db_manager.get_user(member.id)
            if user_data:
                new_warnings = user_data.get('warnings', 0) + 1
                await self.bot.db_manager.execute(
                    "UPDATE users SET warnings = $1 WHERE id = $2",
                    new_warnings, member.id
                )
            
            # Create response embed
            response_embed = create_embed(
                title="⚠️ User Warned",
                fields=[
                    {"name": "User", "value": member.mention, "inline": True},
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                    {"name": "Infraction ID", "value": str(infraction_id), "inline": True}
                ],
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=response_embed)
            
            # Log the action
            self.logger.moderation_action("warn", ctx.author, member, reason)
            
        except Exception as e:
            self.logger.error(f"Error warning user {member.id}: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to warn the user.")
    
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str = "1h", *, reason: str = "No reason provided"):
        """
        Mute a member for a specified duration.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member): Member to mute
            duration (str): Duration for the mute (e.g., 1h, 30m, 1d)
            reason (str): Reason for the mute
        """
        # Check if user is trying to mute themselves
        if member.id == ctx.author.id:
            await ctx.send("You cannot mute yourself.")
            return
        
        # Check if user is trying to mute the bot
        if member.id == self.bot.user.id:
            await ctx.send("I cannot mute myself.")
            return
        
        # Check hierarchy
        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot mute someone with a higher or equal role.")
            return
        
        # Parse duration
        parsed_duration = parse_duration(duration)
        if not parsed_duration:
            await ctx.send("Invalid duration format. Use formats like: 1h, 30m, 1d, 2h30m")
            return
        
        if parsed_duration.total_seconds() > 2419200:  # 28 days max
            await ctx.send("Maximum mute duration is 28 days.")
            return
        
        # Find or create mute role
        mute_role = None
        for role in ctx.guild.roles:
            if "mute" in role.name.lower() or "muted" in role.name.lower():
                mute_role = role
                break
        
        if not mute_role:
            # Create mute role
            try:
                mute_role = await ctx.guild.create_role(
                    name="Muted",
                    reason="Mute system - automatically created"
                )
                
                # Set permissions for the mute role in all text channels
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(
                        mute_role,
                        send_messages=False,
                        add_reactions=False
                    )
                
                # Set permissions for the mute role in all voice channels
                for channel in ctx.guild.voice_channels:
                    await channel.set_permissions(
                        mute_role,
                        speak=False,
                        connect=False
                    )
                
                await ctx.send(f"Created Muted role: {mute_role.mention}")
            except discord.Forbidden:
                await ctx.send("I don't have permission to create a mute role.")
                return
            except Exception as e:
                self.logger.error(f"Error creating mute role: {e}", exc_info=True)
                await ctx.send("Error creating mute role.")
                return
        
        try:
            # Add mute role to member
            await member.add_roles(mute_role, reason=f"Muted by {ctx.author}: {reason}")
            
            # Calculate unmute time
            unmute_time = datetime.utcnow() + parsed_duration
            
            # Create DM embed
            mute_embed = create_embed(
                title="🔇 Muted",
                description=f"You have been muted in {ctx.guild.name}",
                fields=[
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Duration", "value": duration, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                    {"name": "Unmute Time", "value": f"<t:{int(unmute_time.timestamp())}:F>", "inline": False}
                ],
                color=discord.Color.red()
            )
            
            # Try to send DM to the user
            try:
                await member.send(embed=mute_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Log the mute in the database
            infraction_id = await self.bot.db_manager.log_moderation_action(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                action_type="mute",
                reason=reason,
                duration=int(parsed_duration.total_seconds())
            )
            
            # Create response embed
            response_embed = create_embed(
                title="🔇 User Muted",
                fields=[
                    {"name": "User", "value": member.mention, "inline": True},
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Duration", "value": duration, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                    {"name": "Infraction ID", "value": str(infraction_id), "inline": True}
                ],
                color=discord.Color.red()
            )
            
            await ctx.send(embed=response_embed)
            
            # Log the action
            self.logger.moderation_action("mute", ctx.author, member, reason)
            
            # Schedule unmute
            await self.schedule_unmute(member.id, mute_role.id, parsed_duration.total_seconds())
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to mute this user.")
        except Exception as e:
            self.logger.error(f"Error muting user {member.id}: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to mute the user.")
    
    async def schedule_unmute(self, user_id: int, role_id: int, duration_seconds: int):
        """
        Schedule an unmute operation after the specified duration.
        
        Args:
            user_id (int): User ID to unmute
            role_id (int): Role ID to remove
            duration_seconds (int): Duration in seconds
        """
        # This is a simplified version - in a real implementation you'd want to use
        # a proper task scheduler or database-based timer system
        await asyncio.sleep(duration_seconds)
        
        # Find the guild and member
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                role = discord.utils.get(guild.roles, id=role_id)
                if role:
                    try:
                        await member.remove_roles(role, reason="Mute duration expired")
                        
                        # Send DM notification
                        unmute_embed = create_embed(
                            title="🔊 Unmuted",
                            description=f"Your mute in {guild.name} has expired.",
                            color=discord.Color.green()
                        )
                        
                        try:
                            await member.send(embed=unmute_embed)
                        except discord.Forbidden:
                            pass
                        
                        self.logger.info(f"Auto-unmuted user {user_id} after {duration_seconds}s")
                        break
                    except Exception as e:
                        self.logger.error(f"Error auto-unmuting user {user_id}: {e}", exc_info=True)
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Kick a member from the server.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member): Member to kick
            reason (str): Reason for the kick
        """
        # Check if user is trying to kick themselves
        if member.id == ctx.author.id:
            await ctx.send("You cannot kick yourself.")
            return
        
        # Check if user is trying to kick the bot
        if member.id == self.bot.user.id:
            await ctx.send("I cannot kick myself.")
            return
        
        # Check hierarchy
        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot kick someone with a higher or equal role.")
            return
        
        try:
            # Create DM embed
            kick_embed = create_embed(
                title="👢 Kicked",
                description=f"You have been kicked from {ctx.guild.name}",
                fields=[
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False}
                ],
                color=discord.Color.red()
            )
            
            # Try to send DM to the user
            try:
                await member.send(embed=kick_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Kick the member
            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            
            # Log the kick in the database
            infraction_id = await self.bot.db_manager.log_moderation_action(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                action_type="kick",
                reason=reason
            )
            
            # Create response embed
            response_embed = create_embed(
                title="👢 User Kicked",
                fields=[
                    {"name": "User", "value": f"{member.mention} ({member})", "inline": True},
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                    {"name": "Infraction ID", "value": str(infraction_id), "inline": True}
                ],
                color=discord.Color.red()
            )
            
            await ctx.send(embed=response_embed)
            
            # Log the action
            self.logger.moderation_action("kick", ctx.author, member, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick this user.")
        except Exception as e:
            self.logger.error(f"Error kicking user {member.id}: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to kick the user.")
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """
        Ban a member from the server.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member): Member to ban
            reason (str): Reason for the ban
        """
        # Check if user is trying to ban themselves
        if member.id == ctx.author.id:
            await ctx.send("You cannot ban yourself.")
            return
        
        # Check if user is trying to ban the bot
        if member.id == self.bot.user.id:
            await ctx.send("I cannot ban myself.")
            return
        
        # Check hierarchy
        if ctx.author.top_role <= member.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("You cannot ban someone with a higher or equal role.")
            return
        
        try:
            # Create DM embed
            ban_embed = create_embed(
                title="🔨 Banned",
                description=f"You have been banned from {ctx.guild.name}",
                fields=[
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False}
                ],
                color=discord.Color.red()
            )
            
            # Try to send DM to the user
            try:
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Ban the member
            await member.ban(reason=f"Banned by {ctx.author}: {reason}")
            
            # Log the ban in the database
            infraction_id = await self.bot.db_manager.log_moderation_action(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                action_type="ban",
                reason=reason
            )
            
            # Create response embed
            response_embed = create_embed(
                title="🔨 User Banned",
                fields=[
                    {"name": "User", "value": f"{member.mention} ({member})", "inline": True},
                    {"name": "Moderator", "value": ctx.author.mention, "inline": True},
                    {"name": "Reason", "value": reason, "inline": False},
                    {"name": "Infraction ID", "value": str(infraction_id), "inline": True}
                ],
                color=discord.Color.red()
            )
            
            await ctx.send(embed=response_embed)
            
            # Log the action
            self.logger.moderation_action("ban", ctx.author, member, reason)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this user.")
        except Exception as e:
            self.logger.error(f"Error banning user {member.id}: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to ban the user.")
    
    @commands.command(name='infractions', aliases=['warnings', 'history'])
    async def infractions(self, ctx: commands.Context, member: discord.Member = None):
        """
        View a user's moderation history.
        
        Args:
            ctx (commands.Context): Command context
            member (discord.Member, optional): Member to check history for (defaults to command author)
        """
        if member is None:
            member = ctx.author
        
        try:
            # Get user's infractions from database
            infractions = await self.bot.db_manager.get_user_infractions(member.id)
            
            if not infractions:
                embed = create_embed(
                    title=f"📋 {member.display_name}'s Infraction History",
                    description="No infractions found.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed with infractions
            embed = create_embed(
                title=f"📋 {member.display_name}'s Infraction History",
                description=f"Total infractions: {len(infractions)}",
                color=discord.Color.orange()
            )
            
            # Add fields for each infraction (limit to 5 to avoid embed size limits)
            for i, infraction in enumerate(infractions[:5]):
                action_type = infraction['action_type'].upper()
                timestamp = infraction['created_at']
                reason = infraction['reason'] or "No reason provided"
                
                # Get moderator who performed the action
                moderator = ctx.guild.get_member(infraction['moderator_id'])
                moderator_name = moderator.mention if moderator else f"<@{infraction['moderator_id']}>"
                
                embed.add_field(
                    name=f"#{len(infractions) - i}: {action_type}",
                    value=(
                        f"**Moderator:** {moderator_name}\n"
                        f"**Reason:** {reason}\n"
                        f"**Date:** <t:{int(timestamp.timestamp())}:F>"
                    ),
                    inline=False
                )
            
            if len(infractions) > 5:
                embed.set_footer(text=f"Showing latest 5 of {len(infractions)} total infractions")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error fetching infractions for user {member.id}: {e}", exc_info=True)
            await ctx.send("An error occurred while fetching the infraction history.")


async def setup(bot):
    """
    Set up the punishment system cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(PunishmentSystem(bot))