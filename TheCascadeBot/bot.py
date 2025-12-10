"""
The Cascade Bot - Production-Ready Discord Bot
Main Entry Point

This is the main entry point for the enterprise-grade Discord bot that includes
moderation, logging, fun, and utility features with PostgreSQL, Redis, and advanced
security measures.
"""

import os
import sys
import asyncio
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands
import asyncpg
import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configuration and constants
from config.settings import Settings
from core.logger import setup_logging
from core.database import DatabaseManager
from core.cache import CacheManager
from core.bot import TheCascadeBot


def main():
    """
    Main entry point for The Cascade Bot.
    
    Initializes all core systems, connects to databases, loads cogs,
    and starts the bot.
    """
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting The Cascade Bot v1.0")
    logger.info(f"Initialization Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Initialize settings
        settings = Settings()
        
        # Validate configuration before proceeding
        settings.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize bot instance
        intents = discord.Intents.default()
        intents.message_content = True  # Required for moderation
        intents.members = True          # Required for member tracking
        intents.guilds = True           # Required for server events
        intents.voice_states = True     # Required for voice tracking
        intents.bans = True             # Required for ban logs
        intents.presences = True        # Required for presence tracking
        
        bot = TheCascadeBot(
            command_prefix=settings.COMMAND_PREFIX,
            intents=intents,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions.none(),
            help_command=None,  # Using custom help system
            max_messages=10000,  # Cache recent messages for moderation
            chunk_guilds_at_startup=False  # Don't fetch all members at startup
        )
        
        # Store settings in bot instance
        bot.settings = settings
        
        # Initialize database connection
        logger.info("Connecting to PostgreSQL database...")
        db_manager = DatabaseManager(settings.DATABASE_URL)
        bot.db_manager = db_manager
        
        # Initialize Redis cache
        logger.info("Connecting to Redis cache...")
        cache_manager = CacheManager(settings.REDIS_URL)
        bot.cache_manager = cache_manager
        
        # Connect to databases
        asyncio.run(db_manager.connect())
        asyncio.run(cache_manager.connect())
        
        logger.info("Database and cache connections established")
        
        # Load all cogs
        logger.info("Loading cogs...")
        load_cogs(bot)
        
        logger.info("All systems initialized. Starting bot...")
        
        # Start the bot
        bot.run(settings.DISCORD_TOKEN, reconnect=True)
        
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received. Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"Critical error during initialization: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup connections
        if 'db_manager' in locals():
            try:
                asyncio.run(db_manager.close())
            except:
                pass
        if 'cache_manager' in locals():
            try:
                asyncio.run(cache_manager.close())
            except:
                pass
        logger.info("Shutdown complete")


def load_cogs(bot):
    """
    Dynamically load all available cogs from the cogs directory.
    
    Args:
        bot (TheCascadeBot): The bot instance to load cogs into
    """
    logger = logging.getLogger(__name__)
    
    # Define the cog loading order to ensure dependencies are met
    cog_directories = [
        'cogs.system',
        'cogs.moderation',
        'cogs.logging',
        'cogs.utility', 
        'cogs.fun'
    ]
    
    loaded_cogs = []
    
    for cog_dir in cog_directories:
        cog_path = Path(cog_dir.replace('.', '/'))
        
        if cog_path.exists() and cog_path.is_dir():
            # Look for all Python files in the directory
            for py_file in cog_path.glob('*.py'):
                if py_file.name.startswith('__'):
                    continue
                    
                cog_name = f"{cog_dir}.{py_file.stem}"
                
                try:
                    bot.load_extension(cog_name)
                    loaded_cogs.append(cog_name)
                    logger.info(f"Successfully loaded cog: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_name}: {e}")
        else:
            logger.warning(f"Cog directory does not exist: {cog_dir}")
    
    logger.info(f"Loaded {len(loaded_cogs)} cogs: {', '.join(loaded_cogs)}")


if __name__ == "__main__":
    main()