"""
Logging system for The Cascade Bot.

This module sets up comprehensive logging with file rotation, console output,
and different log levels for different components.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging():
    """
    Set up the logging system for the bot.
    
    Configures both file and console logging with appropriate formatting
    and log levels. Creates log directories if they don't exist.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Discord-specific logging
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    
    print(f"Logging initialized with level: {log_level}")
    print(f"Log file: {logs_dir / f'bot_{datetime.now().strftime('%Y%m%d')}.log'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name (str): Name of the logger (typically __name__ of the module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class BotLogger:
    """
    Enhanced logging class with bot-specific functionality.
    
    Provides additional logging methods specific to bot operations.
    """
    
    def __init__(self, name: str):
        """
        Initialize the BotLogger.
        
        Args:
            name (str): Name of the logger
        """
        self.logger = get_logger(name)
    
    def command_used(self, ctx, command_name: str):
        """
        Log when a command is used.
        
        Args:
            ctx: Command context
            command_name (str): Name of the command that was used
        """
        self.logger.info(
            f"Command '{command_name}' used by {ctx.author} ({ctx.author.id}) "
            f"in channel {ctx.channel} ({ctx.channel.id})"
        )
    
    def moderation_action(self, action: str, moderator, target, reason: str = None):
        """
        Log a moderation action.
        
        Args:
            action (str): Type of moderation action (warn, mute, kick, ban, etc.)
            moderator: User who performed the action
            target: User who was targeted by the action
            reason (str, optional): Reason for the action
        """
        reason_str = f" with reason: '{reason}'" if reason else ""
        self.logger.info(
            f"Moderation action '{action}' performed by {moderator} ({moderator.id}) "
            f"on {target} ({target.id}){reason_str}"
        )
    
    def error_occurred(self, error, context=None):
        """
        Log an error with appropriate context.
        
        Args:
            error: The error that occurred
            context: Optional context information
        """
        context_str = f" in context: {context}" if context else ""
        self.logger.error(f"Error occurred{context_str}: {error}", exc_info=True)
    
    def debug_info(self, message: str, extra_data: dict = None):
        """
        Log debug information with optional extra data.
        
        Args:
            message (str): Debug message
            extra_data (dict, optional): Additional data to log
        """
        if extra_data:
            self.logger.debug(f"{message} - Extra data: {extra_data}")
        else:
            self.logger.debug(message)
    
    # Standard logging methods
    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log an error message."""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str):
        """Log a critical message."""
        self.logger.critical(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)