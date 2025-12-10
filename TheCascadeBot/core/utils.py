"""
Utility functions for The Cascade Bot.

This module contains various utility functions that are used throughout
the bot for common operations like validation, formatting, and helpers.
"""

import re
import time
import asyncio
from typing import Union, Optional, List, Dict, Any
from datetime import datetime, timedelta
import discord
from discord.ext import commands


def is_valid_discord_id(id_str: str) -> bool:
    """
    Check if a string is a valid Discord ID.
    
    Args:
        id_str (str): String to validate
        
    Returns:
        bool: True if valid Discord ID, False otherwise
    """
    try:
        # Discord IDs are 17-20 digits long
        id_int = int(id_str)
        return 17 <= len(str(id_int)) <= 20
    except ValueError:
        return False


def format_timedelta(td: timedelta) -> str:
    """
    Format a timedelta object into a human-readable string.
    
    Args:
        td (timedelta): Timedelta object to format
        
    Returns:
        str: Formatted time string
    """
    total_seconds = int(td.total_seconds())
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parse a duration string into a timedelta object.
    
    Supports formats like: 1d, 2h, 30m, 45s, 1d2h30m, etc.
    
    Args:
        duration_str (str): Duration string to parse
        
    Returns:
        Optional[timedelta]: Parsed duration or None if invalid
    """
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, duration_str.lower().strip())
    
    if not match:
        return None
    
    days, hours, minutes, seconds = match.groups(default='0')
    
    try:
        return timedelta(
            days=int(days),
            hours=int(hours),
            minutes=int(minutes),
            seconds=int(seconds)
        )
    except ValueError:
        return None


def escape_mentions(text: str) -> str:
    """
    Escape Discord mentions in a text string.
    
    Args:
        text (str): Text to escape mentions in
        
    Returns:
        str: Text with mentions escaped
    """
    # Escape @everyone and @here
    text = text.replace('@everyone', '@\u200beveryone')
    text = text.replace('@here', '@\u200bhere')
    
    # Escape user and role mentions
    mention_pattern = re.compile(r'<(@[!&]?|#)(\d+)>')
    text = mention_pattern.sub(r'<\1\u200b\2>', text)
    
    return text


def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue(), 
                fields: List[Dict[str, Any]] = None, footer: str = "", 
                timestamp: bool = True) -> discord.Embed:
    """
    Create a standardized embed with common formatting.
    
    Args:
        title (str): Embed title
        description (str): Embed description
        color (discord.Color): Embed color
        fields (List[Dict[str, Any]]): List of field dictionaries with 'name' and 'value'
        footer (str): Footer text
        timestamp (bool): Whether to include timestamp
        
    Returns:
        discord.Embed: Formatted embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow() if timestamp else None
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get('name', '\u200b'),  # Zero-width space for empty name
                value=field.get('value', '\u200b'),  # Zero-width space for empty value
                inline=field.get('inline', True)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed


async def safe_delete_message(message: discord.Message, delay: float = 0) -> bool:
    """
    Safely delete a message with error handling.
    
    Args:
        message (discord.Message): Message to delete
        delay (float): Delay in seconds before deletion
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if delay > 0:
            await asyncio.sleep(delay)
        await message.delete()
        return True
    except discord.NotFound:
        # Message already deleted
        return False
    except discord.Forbidden:
        # Missing permissions
        return False
    except Exception:
        # Other error
        return False


def check_permissions(ctx: commands.Context, **perms) -> bool:
    """
    Check if the user has the specified permissions in the current context.
    
    Args:
        ctx (commands.Context): Command context
        **perms: Permissions to check
        
    Returns:
        bool: True if user has all specified permissions, False otherwise
    """
    if ctx.guild is None:
        # DM context, user has no permissions
        return False
    
    ch = ctx.channel
    permissions = ch.permissions_for(ctx.author)
    
    missing = [perm for perm, value in perms.items() 
               if getattr(permissions, perm, None) != value]
    
    return not missing


def is_mod_or_admin(member: discord.Member, mod_role_id: int = None, 
                   admin_role_id: int = None) -> bool:
    """
    Check if a member is a moderator or admin based on roles.
    
    Args:
        member (discord.Member): Member to check
        mod_role_id (int, optional): Moderator role ID
        admin_role_id (int, optional): Admin role ID
        
    Returns:
        bool: True if member is mod or admin, False otherwise
    """
    if not member.guild:
        return False
    
    # Check if user is guild owner
    if member == member.guild.owner:
        return True
    
    # Check for role IDs if provided
    if mod_role_id and any(role.id == mod_role_id for role in member.roles):
        return True
    
    if admin_role_id and any(role.id == admin_role_id for role in member.roles):
        return True
    
    # Check for built-in permissions
    permissions = member.guild_permissions
    return permissions.administrator or permissions.manage_guild or permissions.ban_members


def get_member_safe(guild: discord.Guild, user_id: int) -> Optional[discord.Member]:
    """
    Safely get a member from a guild, falling back to fetching if not cached.
    
    Args:
        guild (discord.Guild): Guild to search in
        user_id (int): User ID to look for
        
    Returns:
        Optional[discord.Member]: Member if found, None otherwise
    """
    member = guild.get_member(user_id)
    if member:
        return member
    
    try:
        # Try to fetch the member
        return guild.get_member_named(str(user_id))
    except:
        return None


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for safe processing.
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potentially harmful characters/sequences
    # This is a basic sanitization - expand as needed
    text = text.replace('\0', '')  # Null bytes
    text = text.replace('\x00', '')  # Another null byte form
    
    return text.strip()


def calculate_xp_needed(level: int) -> int:
    """
    Calculate the XP needed to reach the next level.
    
    Args:
        level (int): Current level
        
    Returns:
        int: XP needed for next level
    """
    # Formula: XP needed = 50 * (level ^ 2) + 100 * level + 50
    return 50 * (level ** 2) + 100 * level + 50


def get_level_from_xp(xp: int) -> int:
    """
    Calculate the level from XP.
    
    Args:
        xp (int): Total XP
        
    Returns:
        int: Current level
    """
    # This is an inverse of the calculate_xp_needed function
    level = 0
    while xp >= calculate_xp_needed(level):
        xp -= calculate_xp_needed(level)
        level += 1
    return level


def format_number(num: Union[int, float]) -> str:
    """
    Format a number with commas for thousands.
    
    Args:
        num (Union[int, float]): Number to format
        
    Returns:
        str: Formatted number string
    """
    if isinstance(num, float):
        return f"{num:,.2f}"
    return f"{num:,}"


def get_top_role(member: discord.Member) -> discord.Role:
    """
    Get the highest role of a member.
    
    Args:
        member (discord.Member): Member to get top role for
        
    Returns:
        discord.Role: Highest role of the member
    """
    return member.top_role if member.roles else None


def is_valid_emoji(emoji: str) -> bool:
    """
    Check if a string is a valid emoji.
    
    Args:
        emoji (str): Emoji string to validate
        
    Returns:
        bool: True if valid emoji, False otherwise
    """
    # This is a simplified check - expand as needed
    # Check for standard Unicode emojis
    try:
        return len(emoji.encode('utf-8')) <= 4
    except:
        return False


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst (List[Any]): List to chunk
        chunk_size (int): Size of each chunk
        
    Returns:
        List[List[Any]]: List of chunked sublists
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def time_since(dt: datetime) -> str:
    """
    Calculate a "time since" statement for a datetime.
    
    Args:
        dt (datetime): Datetime to calculate from
        
    Returns:
        str: Time since statement
    """
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    return "Just now"