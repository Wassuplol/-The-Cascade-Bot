"""
Cache manager for The Cascade Bot.

This module handles Redis caching for high-frequency operations,
temporary data storage, and performance optimization.
"""

import redis.asyncio as redis
import logging
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta


class CacheManager:
    """
    Asynchronous cache manager for Redis operations.
    
    Handles caching of frequently accessed data, temporary storage,
    and performance optimization using Redis.
    """
    
    def __init__(self, redis_url: str, db: int = 0, password: Optional[str] = None):
        """
        Initialize the cache manager.
        
        Args:
            redis_url (str): Redis server URL
            db (int): Redis database number
            password (str, optional): Redis password
        """
        self.redis_url = redis_url
        self.db = db
        self.password = password
        self.redis: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """
        Establish connection to the Redis server.
        """
        try:
            self.redis = redis.Redis(
                from_url=self.redis_url,
                db=self.db,
                password=self.password,
                decode_responses=False,  # We'll handle decoding manually
                health_check_interval=30
            )
            
            # Test the connection
            await self.redis.ping()
            self.logger.info("Successfully connected to Redis cache")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """
        Close the Redis connection.
        """
        if self.redis:
            await self.redis.close()
            self.logger.info("Redis connection closed")
    
    async def set(self, key: str, value: Any, expire: Union[int, timedelta, None] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            expire (Union[int, timedelta, None]): Expiration time in seconds or timedelta
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            # Serialize the value to bytes
            serialized_value = pickle.dumps(value)
            
            if expire is not None:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                result = await self.redis.setex(key, expire, serialized_value)
            else:
                result = await self.redis.set(key, serialized_value)
            
            return result is not None
        except Exception as e:
            self.logger.error(f"Cache set error for key '{key}': {e}", exc_info=True)
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key (str): Cache key
            default (Any): Default value if key doesn't exist
            
        Returns:
            Any: Cached value or default
        """
        if not self.redis:
            return default
        
        try:
            value = await self.redis.get(key)
            if value is not None:
                return pickle.loads(value)
            return default
        except Exception as e:
            self.logger.error(f"Cache get error for key '{key}': {e}", exc_info=True)
            return default
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key (str): Cache key to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Cache delete error for key '{key}': {e}", exc_info=True)
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key (str): Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            self.logger.error(f"Cache exists error for key '{key}': {e}", exc_info=True)
            return False
    
    async def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key (str): Cache key
            time (Union[int, timedelta]): Expiration time in seconds or timedelta
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            if isinstance(time, timedelta):
                time = int(time.total_seconds())
            result = await self.redis.expire(key, time)
            return result
        except Exception as e:
            self.logger.error(f"Cache expire error for key '{key}': {e}", exc_info=True)
            return False
    
    async def keys(self, pattern: str = "*") -> list:
        """
        Get all keys matching a pattern.
        
        Args:
            pattern (str): Key pattern to match (default is "*")
            
        Returns:
            list: List of matching keys
        """
        if not self.redis:
            return []
        
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            self.logger.error(f"Cache keys error for pattern '{pattern}': {e}", exc_info=True)
            return []
    
    async def flush_all(self) -> bool:
        """
        Delete all keys in the current database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            return False
        
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Cache flush_all error: {e}", exc_info=True)
            return False
    
    # Bot-specific caching methods
    async def cache_user_data(self, user_id: int, data: dict, ttl: int = 3600) -> bool:
        """
        Cache user data with a specific TTL.
        
        Args:
            user_id (int): Discord user ID
            data (dict): User data to cache
            ttl (int): Time to live in seconds (default 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"user:{user_id}"
        return await self.set(key, data, ttl)
    
    async def get_cached_user_data(self, user_id: int) -> Optional[dict]:
        """
        Get cached user data.
        
        Args:
            user_id (int): Discord user ID
            
        Returns:
            Optional[dict]: Cached user data or None
        """
        key = f"user:{user_id}"
        return await self.get(key)
    
    async def cache_guild_config(self, guild_id: int, config: dict, ttl: int = 7200) -> bool:
        """
        Cache guild configuration.
        
        Args:
            guild_id (int): Discord guild ID
            config (dict): Guild configuration
            ttl (int): Time to live in seconds (default 2 hours)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"guild:{guild_id}:config"
        return await self.set(key, config, ttl)
    
    async def get_cached_guild_config(self, guild_id: int) -> Optional[dict]:
        """
        Get cached guild configuration.
        
        Args:
            guild_id (int): Discord guild ID
            
        Returns:
            Optional[dict]: Cached guild configuration or None
        """
        key = f"guild:{guild_id}:config"
        return await self.get(key)
    
    async def cache_command_cooldown(self, user_id: int, command_name: str, ttl: int = 60) -> bool:
        """
        Cache a command cooldown.
        
        Args:
            user_id (int): Discord user ID
            command_name (str): Command name
            ttl (int): Time to live in seconds (default 1 minute)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"cooldown:{user_id}:{command_name}"
        return await self.set(key, True, ttl)
    
    async def is_command_on_cooldown(self, user_id: int, command_name: str) -> bool:
        """
        Check if a command is on cooldown for a user.
        
        Args:
            user_id (int): Discord user ID
            command_name (str): Command name
            
        Returns:
            bool: True if on cooldown, False otherwise
        """
        key = f"cooldown:{user_id}:{command_name}"
        return await self.exists(key)
    
    async def cache_message_content(self, message_id: int, content: str, ttl: int = 86400) -> bool:
        """
        Cache message content (useful for edit/delete logging).
        
        Args:
            message_id (int): Discord message ID
            content (str): Message content
            ttl (int): Time to live in seconds (default 24 hours)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"message:{message_id}:content"
        return await self.set(key, content, ttl)
    
    async def get_cached_message_content(self, message_id: int) -> Optional[str]:
        """
        Get cached message content.
        
        Args:
            message_id (int): Discord message ID
            
        Returns:
            Optional[str]: Cached message content or None
        """
        key = f"message:{message_id}:content"
        return await self.get(key)
    
    async def cache_member_roles(self, member_id: int, roles: list, ttl: int = 300) -> bool:
        """
        Cache member roles.
        
        Args:
            member_id (int): Discord member ID
            roles (list): List of role IDs
            ttl (int): Time to live in seconds (default 5 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        key = f"member:{member_id}:roles"
        return await self.set(key, roles, ttl)
    
    async def get_cached_member_roles(self, member_id: int) -> Optional[list]:
        """
        Get cached member roles.
        
        Args:
            member_id (int): Discord member ID
            
        Returns:
            Optional[list]: Cached roles or None
        """
        key = f"member:{member_id}:roles"
        return await self.get(key)
    
    async def increment_counter(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """
        Increment a counter in the cache.
        
        Args:
            key (str): Counter key
            amount (int): Amount to increment by (default 1)
            ttl (int, optional): Time to live in seconds
            
        Returns:
            int: New counter value
        """
        if not self.redis:
            return 0
        
        try:
            result = await self.redis.incrby(key, amount)
            if ttl:
                await self.redis.expire(key, ttl)
            return result
        except Exception as e:
            self.logger.error(f"Cache increment error for key '{key}': {e}", exc_info=True)
            return 0
    
    async def get_counter(self, key: str) -> int:
        """
        Get the value of a counter.
        
        Args:
            key (str): Counter key
            
        Returns:
            int: Counter value or 0 if not found
        """
        if not self.redis:
            return 0
        
        try:
            value = await self.redis.get(key)
            return int(value) if value else 0
        except Exception as e:
            self.logger.error(f"Cache get_counter error for key '{key}': {e}", exc_info=True)
            return 0