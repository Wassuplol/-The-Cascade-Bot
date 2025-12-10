"""
Configuration settings for The Cascade Bot.

This module handles loading and validation of environment variables and
configuration settings for the bot.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Settings:
    """
    Configuration settings for The Cascade Bot.
    
    This class loads configuration from environment variables and provides
    validation for required settings.
    """
    
    # Discord settings
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    COMMAND_PREFIX: str = os.getenv('COMMAND_PREFIX', '!')
    BOT_OWNER_ID: Optional[int] = int(os.getenv('BOT_OWNER_ID', '0')) if os.getenv('BOT_OWNER_ID') else None
    GUILD_ID: Optional[int] = int(os.getenv('GUILD_ID', '0')) if os.getenv('GUILD_ID') else None
    
    # Database settings
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/thecascade')
    DATABASE_POOL_MIN: int = int(os.getenv('DATABASE_POOL_MIN', '5'))
    DATABASE_POOL_MAX: int = int(os.getenv('DATABASE_POOL_MAX', '20'))
    
    # Redis settings
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD', None)
    
    # API Keys
    PERSPECTIVE_API_KEY: Optional[str] = os.getenv('PERSPECTIVE_API_KEY')
    
    # Bot settings
    MAX_MESSAGE_CACHE: int = int(os.getenv('MAX_MESSAGE_CACHE', '10000'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # Moderation settings
    SPAM_THRESHOLD_MESSAGES: int = int(os.getenv('SPAM_THRESHOLD_MESSAGES', '5'))
    SPAM_THRESHOLD_SECONDS: int = int(os.getenv('SPAM_THRESHOLD_SECONDS', '10'))
    TOXICITY_THRESHOLD: float = float(os.getenv('TOXICITY_THRESHOLD', '0.7'))
    
    # Rate limiting
    GLOBAL_RATE_LIMIT: int = int(os.getenv('GLOBAL_RATE_LIMIT', '10'))  # requests per minute
    
    def validate(self) -> None:
        """
        Validate that all required settings are present and correctly formatted.
        
        Raises:
            ValueError: If any required setting is missing or invalid
        """
        errors = []
        
        # Validate Discord token
        if not self.DISCORD_TOKEN or len(self.DISCORD_TOKEN.strip()) == 0:
            errors.append("DISCORD_TOKEN is required")
        
        # Validate command prefix
        if not self.COMMAND_PREFIX or len(self.COMMAND_PREFIX.strip()) == 0:
            errors.append("COMMAND_PREFIX is required")
        
        # Validate database URL
        if not self.DATABASE_URL or len(self.DATABASE_URL.strip()) == 0:
            errors.append("DATABASE_URL is required")
        
        # Validate Redis URL
        if not self.REDIS_URL or len(self.REDIS_URL.strip()) == 0:
            errors.append("REDIS_URL is required")
        
        # Validate numeric settings
        if self.DATABASE_POOL_MIN <= 0:
            errors.append("DATABASE_POOL_MIN must be greater than 0")
        
        if self.DATABASE_POOL_MAX <= 0:
            errors.append("DATABASE_POOL_MAX must be greater than 0")
        
        if self.DATABASE_POOL_MIN > self.DATABASE_POOL_MAX:
            errors.append("DATABASE_POOL_MIN cannot be greater than DATABASE_POOL_MAX")
        
        if self.SPAM_THRESHOLD_MESSAGES <= 0:
            errors.append("SPAM_THRESHOLD_MESSAGES must be greater than 0")
        
        if self.SPAM_THRESHOLD_SECONDS <= 0:
            errors.append("SPAM_THRESHOLD_SECONDS must be greater than 0")
        
        if self.TOXICITY_THRESHOLD < 0 or self.TOXICITY_THRESHOLD > 1:
            errors.append("TOXICITY_THRESHOLD must be between 0 and 1")
        
        if self.GLOBAL_RATE_LIMIT <= 0:
            errors.append("GLOBAL_RATE_LIMIT must be greater than 0")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    def get_database_config(self) -> dict:
        """
        Get database configuration dictionary for asyncpg.
        
        Returns:
            dict: Configuration dictionary for asyncpg.create_pool
        """
        return {
            'min_size': self.DATABASE_POOL_MIN,
            'max_size': self.DATABASE_POOL_MAX,
            'command_timeout': 60,
        }