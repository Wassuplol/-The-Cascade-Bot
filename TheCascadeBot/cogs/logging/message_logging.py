"""
Message logging cog for The Cascade Bot.

This module implements logging for message deletions, edits, and other
message-related events with comprehensive information storage.
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime
from core.utils import create_embed, escape_mentions
from core.logger import BotLogger


class MessageLogging(commands.Cog):
    """
    Message logging cog implementing logging for message deletions, edits, and other events.
    """
    
    def __init__(self, bot):
        """
        Initialize the message logging cog.
        
        Args:
            bot: The bot instance
        """
        self.bot = bot
        self.logger = BotLogger(__name__)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log when a message is deleted.
        
        Args:
            message (discord.Message): The deleted message
        """
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        try:
            # Get guild config to determine log channel
            guild_config = await self.bot.db_manager.get_server_config(message.guild.id)
            log_channel_id = guild_config.get('log_channel_id') if guild_config else None
            
            if not log_channel_id:
                return  # No log channel configured
            
            log_channel = message.guild.get_channel(log_channel_id)
            if not log_channel:
                return  # Log channel doesn't exist
            
            # Create embed for the log
            embed = create_embed(
                title="🗑️ Message Deleted",
                fields=[
                    {"name": "Author", "value": f"{message.author.mention} ({message.author})", "inline": True},
                    {"name": "Channel", "value": f"{message.channel.mention} ({message.channel.name})", "inline": True},
                    {"name": "Message ID", "value": str(message.id), "inline": True},
                    {"name": "Content", "value": escape_mentions(message.content[:1000] or "*(No content - possibly an embed or attachment only)*"), "inline": False}
                ],
                color=discord.Color.red(),
                timestamp=True
            )
            
            # Add attachment info if present
            if message.attachments:
                attachment_names = [f"[{attachment.filename}]" for attachment in message.attachments]
                embed.add_field(
                    name="Attachments", 
                    value=", ".join(attachment_names),
                    inline=False
                )
            
            # Send the log message
            await log_channel.send(embed=embed)
            
            # Also log to database
            await self.bot.db_manager.execute("""
                INSERT INTO message_logs (guild_id, channel_id, user_id, message_id, content, action_type)
                VALUES ($1, $2, $3, $4, $5, 'delete')
            """, message.guild.id, message.channel.id, message.author.id, message.id, message.content)
            
            self.logger.info(f"Logged message deletion: {message.id} by {message.author}")
            
        except Exception as e:
            self.logger.error(f"Error logging message deletion: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Log when a message is edited.
        
        Args:
            before (discord.Message): Message before edit
            after (discord.Message): Message after edit
        """
        # Ignore bot messages and DMs
        if before.author.bot or not before.guild:
            return
        
        # Don't log if content hasn't changed
        if before.content == after.content:
            return
        
        try:
            # Get guild config to determine log channel
            guild_config = await self.bot.db_manager.get_server_config(before.guild.id)
            log_channel_id = guild_config.get('log_channel_id') if guild_config else None
            
            if not log_channel_id:
                return  # No log channel configured
            
            log_channel = before.guild.get_channel(log_channel_id)
            if not log_channel:
                return  # Log channel doesn't exist
            
            # Create embed for the log
            embed = create_embed(
                title="✏️ Message Edited",
                fields=[
                    {"name": "Author", "value": f"{before.author.mention} ({before.author})", "inline": True},
                    {"name": "Channel", "value": f"{before.channel.mention} ({before.channel.name})", "inline": True},
                    {"name": "Message ID", "value": str(before.id), "inline": True},
                    {"name": "Before", "value": escape_mentions(before.content[:500] or "*(No content)*"), "inline": False},
                    {"name": "After", "value": escape_mentions(after.content[:500] or "*(No content)*"), "inline": False}
                ],
                color=discord.Color.orange(),
                timestamp=True
            )
            
            # Send the log message
            await log_channel.send(embed=embed)
            
            # Also log to database
            await self.bot.db_manager.execute("""
                INSERT INTO message_logs (guild_id, channel_id, user_id, message_id, content, action_type)
                VALUES ($1, $2, $3, $4, $5, 'edit')
            """, before.guild.id, before.channel.id, before.author.id, before.id, after.content)
            
            self.logger.info(f"Logged message edit: {before.id} by {before.author}")
            
        except Exception as e:
            self.logger.error(f"Error logging message edit: {e}", exc_info=True)
    
    @commands.command(name='setlogchannel', aliases=['logchannel'])
    @commands.has_permissions(manage_guild=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """
        Set the channel for message logging.
        
        Args:
            ctx (commands.Context): Command context
            channel (discord.TextChannel, optional): Channel to set as log channel (defaults to current channel)
        """
        if channel is None:
            channel = ctx.channel
        
        try:
            # Update server config in database
            await self.bot.db_manager.update_server_config(
                ctx.guild.id,
                log_channel_id=channel.id
            )
            
            # Create confirmation embed
            embed = create_embed(
                title="✅ Log Channel Set",
                description=f"Message logging will now occur in {channel.mention}",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
            self.logger.info(f"Set log channel to {channel.id} in guild {ctx.guild.id}")
            
        except Exception as e:
            self.logger.error(f"Error setting log channel: {e}", exc_info=True)
            await ctx.send("An error occurred while setting the log channel.")
    
    @commands.command(name='messagelog', aliases=['msglog'])
    @commands.has_permissions(manage_messages=True)
    async def message_log(self, ctx: commands.Context, message_id: int):
        """
        View details of a logged message.
        
        Args:
            ctx (commands.Context): Command context
            message_id (int): ID of the message to look up
        """
        try:
            # Look up the message in the database
            record = await self.bot.db_manager.fetchrow("""
                SELECT * FROM message_logs 
                WHERE message_id = $1 AND guild_id = $2
                ORDER BY created_at DESC LIMIT 1
            """, message_id, ctx.guild.id)
            
            if not record:
                await ctx.send("No log found for that message ID.")
                return
            
            # Create embed with message details
            action_type = record['action_type'].upper()
            user = ctx.guild.get_member(record['user_id'])
            user_name = f"{user.mention} ({user})" if user else f"<@{record['user_id']}>"
            
            channel = ctx.guild.get_channel(record['channel_id'])
            channel_name = f"#{channel.name}" if channel else f"<#{record['channel_id']}>"
            
            embed = create_embed(
                title=f"📋 Message Log - {action_type}",
                fields=[
                    {"name": "User", "value": user_name, "inline": True},
                    {"name": "Channel", "value": channel_name, "inline": True},
                    {"name": "Message ID", "value": str(message_id), "inline": True},
                    {"name": "Action", "value": action_type, "inline": True},
                    {"name": "Content", "value": escape_mentions(record['content'] or "*(No content)*"), "inline": False},
                    {"name": "Logged At", "value": f"<t:{int(record['created_at'].timestamp())}:F>", "inline": True}
                ],
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error retrieving message log: {e}", exc_info=True)
            await ctx.send("An error occurred while retrieving the message log.")


async def setup(bot):
    """
    Set up the message logging cog.
    
    Args:
        bot: The bot instance
    """
    await bot.add_cog(MessageLogging(bot))