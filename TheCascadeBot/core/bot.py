"""
Core bot class for The Cascade Bot.

This module extends the discord.ext.commands.Bot class with additional
functionality for enterprise-grade features like error handling,
performance monitoring, and system management.
"""

import discord
from discord.ext import commands
import logging
import time
import asyncio
from typing import Optional, Dict, Any
from core.logger import BotLogger


class TheCascadeBot(commands.Bot):
    """
    Extended Bot class for The Cascade Bot with enterprise features.
    
    Adds additional functionality for logging, error handling, performance
    monitoring, and system management beyond the base commands.Bot class.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the extended bot class.
        
        Args:
            *args: Arguments passed to the parent Bot class
            **kwargs: Keyword arguments passed to the parent Bot class
        """
        super().__init__(*args, **kwargs)
        
        # Initialize custom attributes
        self.start_time = None
        self.logger = BotLogger(__name__)
        self.performance_stats = {
            'commands_executed': 0,
            'messages_processed': 0,
            'events_handled': 0
        }
        
        # Add event listeners
        self.add_listener(self.on_ready, 'on_ready')
        self.add_listener(self.on_command_error, 'on_command_error')
        self.add_listener(self.on_message, 'on_message')
        self.add_listener(self.on_message_delete, 'on_message_delete')
        self.add_listener(self.on_message_edit, 'on_message_edit')
    
    async def setup_hook(self) -> None:
        """
        Called when the bot is starting up and before it logs in.
        
        This is called once the bot's internal state is loaded,
        and before it logs in to Discord.
        """
        self.logger.info("Setting up bot hooks...")
        # Add any setup operations here if needed
        await super().setup_hook()
    
    async def on_ready(self) -> None:
        """
        Called when the bot is ready and connected to Discord.
        """
        self.start_time = time.time()
        self.logger.info(f"{self.user} has connected to Discord!")
        self.logger.info(f"Bot ID: {self.user.id}")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")
        self.logger.info(f"Connected to {len(self.users)} user(s)")
        
        # Log guild information
        for guild in self.guilds:
            self.logger.info(f"- {guild.name} (ID: {guild.id}) - {guild.member_count} members")
    
    async def on_message(self, message: discord.Message) -> None:
        """
        Called when a message is received.
        
        Args:
            message (discord.Message): The received message
        """
        # Ignore messages from bots (including self)
        if message.author.bot:
            return
        
        # Update performance stats
        self.performance_stats['messages_processed'] += 1
        
        # Update user's last seen in cache
        if self.cache_manager:
            await self.cache_manager.update_user_last_seen(message.author.id)
        
        # Process commands
        await self.process_commands(message)
    
    async def process_commands(self, message: discord.Message) -> None:
        """
        Override to add custom command processing logic.
        
        Args:
            message (discord.Message): The message to process commands for
        """
        # Check if message starts with command prefix
        if not message.content.startswith(tuple(self.command_prefix(self, message))):
            return
        
        # Update performance stats
        self.performance_stats['commands_executed'] += 1
        
        # Call parent method to process commands
        await super().process_commands(message)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """
        Handle command errors globally.
        
        Args:
            ctx (commands.Context): Command context
            error (commands.CommandError): The error that occurred
        """
        # Handle specific error types
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command '{ctx.command}' not found.")
            self.logger.warning(f"Command not found: {ctx.command} by {ctx.author}")
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
            self.logger.warning(f"Missing required argument: {error.param.name} in {ctx.command}")
        
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument: {error}")
            self.logger.warning(f"Bad argument in {ctx.command}: {error}")
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
            self.logger.warning(f"Missing permissions for {ctx.command} by {ctx.author}")
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have permission to execute this command.")
            self.logger.warning(f"Bot missing permissions for {ctx.command}")
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f}s")
            self.logger.debug(f"Command on cooldown: {ctx.command} by {ctx.author}")
        
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is currently disabled.")
            self.logger.info(f"Disabled command attempted: {ctx.command}")
        
        else:
            # Log unexpected errors
            self.logger.error_occurred(error, f"Command: {ctx.command}, User: {ctx.author}")
            await ctx.send("An error occurred while executing that command.")
    
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        Called when a message is deleted.
        
        Args:
            message (discord.Message): The deleted message
        """
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Log the deletion
        self.logger.info(f"Message deleted in {message.channel} by {message.author}: {message.content[:100]}...")
        
        # Update performance stats
        self.performance_stats['events_handled'] += 1
    
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        Called when a message is edited.
        
        Args:
            before (discord.Message): Message before edit
            after (discord.Message): Message after edit
        """
        # Ignore bot messages
        if before.author.bot:
            return
        
        # Log the edit
        self.logger.info(f"Message edited in {before.channel} by {before.author}: {before.content[:50]}... -> {after.content[:50]}...")
        
        # Update performance stats
        self.performance_stats['events_handled'] += 1
    
    def get_uptime(self) -> float:
        """
        Get the bot's uptime in seconds.
        
        Returns:
            float: Uptime in seconds, or 0 if not started yet
        """
        if self.start_time:
            return time.time() - self.start_time
        return 0
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the bot.
        
        Returns:
            Dict[str, Any]: Dictionary containing performance statistics
        """
        uptime = self.get_uptime()
        
        return {
            **self.performance_stats,
            'uptime_seconds': uptime,
            'uptime_formatted': self.format_uptime(uptime),
            'latency': f"{self.latency * 1000:.2f}ms"
        }
    
    def format_uptime(self, seconds: float) -> str:
        """
        Format uptime seconds into a human-readable string.
        
        Args:
            seconds (float): Uptime in seconds
            
        Returns:
            str: Formatted uptime string
        """
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.0f}h"
        else:
            days = seconds / 86400
            return f"{days:.0f}d"
    
    async def sync_app_commands(self) -> None:
        """
        Sync application commands (slash commands) with Discord.
        """
        try:
            self.logger.info("Syncing application commands...")
            await self.tree.sync()
            self.logger.info("Application commands synced successfully")
        except Exception as e:
            self.logger.error(f"Failed to sync application commands: {e}", exc_info=True)
    
    async def close(self) -> None:
        """
        Close the bot gracefully, cleaning up resources.
        """
        self.logger.info("Shutting down bot gracefully...")
        
        # Close database connections if they exist
        if hasattr(self, 'db_manager') and self.db_manager:
            await self.db_manager.close()
        
        # Close cache connections if they exist
        if hasattr(self, 'cache_manager') and self.cache_manager:
            await self.cache_manager.close()
        
        # Perform any other cleanup
        self.logger.info("Cleanup complete. Closing bot...")
        await super().close()
    
    def add_command(self, command: commands.Command) -> None:
        """
        Override to add logging for command registration.
        
        Args:
            command (commands.Command): Command to add
        """
        super().add_command(command)
        self.logger.info(f"Registered command: {command.qualified_name}")
    
    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        """
        Override to add logging for cog registration.
        
        Args:
            cog (commands.Cog): Cog to add
            override (bool): Whether to override existing cogs
        """
        super().add_cog(cog, override=override)
        self.logger.info(f"Registered cog: {cog.qualified_name}")