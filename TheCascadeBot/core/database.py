"""
Database manager for The Cascade Bot.

This module handles PostgreSQL database connections, query execution,
and connection pooling using asyncpg for asynchronous operations.
"""

import asyncpg
import logging
from typing import Any, Optional, List, Dict
from contextlib import asynccontextmanager


class DatabaseManager:
    """
    Asynchronous database manager for PostgreSQL operations.
    
    Handles connection pooling, query execution, and transaction management
    for the bot's data storage needs.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the database manager.
        
        Args:
            database_url (str): PostgreSQL database URL
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """
        Establish connection to the PostgreSQL database.
        
        Creates a connection pool with the configured settings.
        """
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'application_name': 'TheCascadeBot',
                    'idle_in_transaction_session_timeout': '60000',  # 60 seconds
                }
            )
            self.logger.info("Successfully connected to PostgreSQL database")
            
            # Initialize database schema
            await self._initialize_schema()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """
        Close the database connection pool.
        """
        if self.pool:
            await self.pool.close()
            self.logger.info("Database connection pool closed")
    
    async def _initialize_schema(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        
        Creates all necessary tables for the bot's functionality.
        """
        self.logger.info("Initializing database schema...")
        
        # Users table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT NOT NULL,
                discriminator TEXT NOT NULL,
                display_name TEXT,
                join_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                xp_points INTEGER DEFAULT 0,
                currency_amount BIGINT DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Moderation logs table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                moderator_id BIGINT NOT NULL,
                action_type TEXT NOT NULL,
                reason TEXT,
                duration INTEGER,  -- Duration in seconds for temp actions
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_guild_user (guild_id, user_id),
                INDEX idx_created_at (created_at)
            )
        """)
        
        # Server configuration table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id BIGINT PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                mod_role_id BIGINT,
                admin_role_id BIGINT,
                mute_role_id BIGINT,
                log_channel_id BIGINT,
                mod_log_channel_id BIGINT,
                welcome_channel_id BIGINT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Custom commands table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS custom_commands (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                command_name TEXT NOT NULL UNIQUE,
                response TEXT NOT NULL,
                created_by BIGINT NOT NULL,
                uses INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_guild_command (guild_id, command_name)
            )
        """)
        
        # Message logs table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS message_logs (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                content TEXT,
                action_type TEXT NOT NULL,  -- 'delete', 'edit'
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_guild_time (guild_id, created_at),
                INDEX idx_message_id (message_id)
            )
        """)
        
        # Reaction roles table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                emoji TEXT NOT NULL,
                role_id BIGINT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_message_emoji (message_id, emoji)
            )
        """)
        
        # User cooldowns table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS user_cooldowns (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                command_name TEXT NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                INDEX idx_user_command (user_id, command_name),
                INDEX idx_expires_at (expires_at)
            )
        """)
        
        self.logger.info("Database schema initialized successfully")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a database connection from the pool.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args) -> Any:
        """
        Execute a query that doesn't return results.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            Any: Result of the query execution
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            return await self.pool.execute(query, *args)
        except Exception as e:
            self.logger.error(f"Database execute error: {e}", exc_info=True)
            raise
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch multiple records from the database.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            List[asyncpg.Record]: List of records
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            return await self.pool.fetch(query, *args)
        except Exception as e:
            self.logger.error(f"Database fetch error: {e}", exc_info=True)
            raise
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch a single record from the database.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            Optional[asyncpg.Record]: Single record or None
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            return await self.pool.fetchrow(query, *args)
        except Exception as e:
            self.logger.error(f"Database fetchrow error: {e}", exc_info=True)
            raise
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch a single value from the database.
        
        Args:
            query (str): SQL query to execute
            *args: Query parameters
            
        Returns:
            Any: Single value or None
        """
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        try:
            return await self.pool.fetchval(query, *args)
        except Exception as e:
            self.logger.error(f"Database fetchval error: {e}", exc_info=True)
            raise
    
    async def create_user(self, user_id: int, username: str, discriminator: str, 
                         display_name: str = None) -> None:
        """
        Create a new user record if it doesn't exist.
        
        Args:
            user_id (int): Discord user ID
            username (str): Discord username
            discriminator (str): Discord discriminator
            display_name (str, optional): Display name
        """
        await self.execute("""
            INSERT INTO users (id, username, discriminator, display_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                discriminator = EXCLUDED.discriminator,
                display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                updated_at = NOW()
        """, user_id, username, discriminator, display_name or username)
    
    async def update_user_last_seen(self, user_id: int) -> None:
        """
        Update the last seen timestamp for a user.
        
        Args:
            user_id (int): Discord user ID
        """
        await self.execute(
            "UPDATE users SET last_seen = NOW() WHERE id = $1",
            user_id
        )
    
    async def add_xp(self, user_id: int, xp: int) -> int:
        """
        Add XP to a user and return the new total.
        
        Args:
            user_id (int): Discord user ID
            xp (int): Amount of XP to add
            
        Returns:
            int: New total XP
        """
        record = await self.fetchrow(
            "UPDATE users SET xp_points = xp_points + $2, updated_at = NOW() WHERE id = $1 RETURNING xp_points",
            user_id, xp
        )
        return record['xp_points'] if record else 0
    
    async def add_currency(self, user_id: int, amount: int) -> int:
        """
        Add currency to a user and return the new balance.
        
        Args:
            user_id (int): Discord user ID
            amount (int): Amount of currency to add
            
        Returns:
            int: New currency balance
        """
        record = await self.fetchrow(
            "UPDATE users SET currency_amount = currency_amount + $2, updated_at = NOW() WHERE id = $1 RETURNING currency_amount",
            user_id, amount
        )
        return record['currency_amount'] if record else 0
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Get user information from the database.
        
        Args:
            user_id (int): Discord user ID
            
        Returns:
            Optional[Dict]: User information or None if not found
        """
        record = await self.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        return dict(record) if record else None
    
    async def log_moderation_action(self, guild_id: int, user_id: int, moderator_id: int, 
                                   action_type: str, reason: str = None, duration: int = None) -> int:
        """
        Log a moderation action to the database.
        
        Args:
            guild_id (int): Discord guild ID
            user_id (int): ID of the user being moderated
            moderator_id (int): ID of the moderator performing the action
            action_type (str): Type of action (warn, mute, kick, ban, etc.)
            reason (str, optional): Reason for the action
            duration (int, optional): Duration of temporary actions in seconds
            
        Returns:
            int: ID of the created log entry
        """
        record = await self.fetchrow("""
            INSERT INTO moderation_logs 
            (guild_id, user_id, moderator_id, action_type, reason, duration)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, guild_id, user_id, moderator_id, action_type, reason, duration)
        
        return record['id'] if record else None
    
    async def get_user_infractions(self, user_id: int) -> List[Dict]:
        """
        Get all moderation infractions for a user.
        
        Args:
            user_id (int): Discord user ID
            
        Returns:
            List[Dict]: List of infraction records
        """
        records = await self.fetch(
            "SELECT * FROM moderation_logs WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )
        return [dict(record) for record in records]
    
    async def get_server_config(self, guild_id: int) -> Optional[Dict]:
        """
        Get server configuration from the database.
        
        Args:
            guild_id (int): Discord guild ID
            
        Returns:
            Optional[Dict]: Server configuration or None if not found
        """
        record = await self.fetchrow(
            "SELECT * FROM server_config WHERE guild_id = $1",
            guild_id
        )
        return dict(record) if record else None
    
    async def update_server_config(self, guild_id: int, **kwargs) -> None:
        """
        Update server configuration in the database.
        
        Args:
            guild_id (int): Discord guild ID
            **kwargs: Configuration values to update
        """
        # Build the SET clause dynamically
        set_parts = []
        values = [guild_id]  # First value is always guild_id
        param_index = 2  # Start from $2 since $1 is guild_id
        
        valid_fields = {
            'prefix', 'mod_role_id', 'admin_role_id', 'mute_role_id', 
            'log_channel_id', 'mod_log_channel_id', 'welcome_channel_id'
        }
        
        for field, value in kwargs.items():
            if field in valid_fields:
                set_parts.append(f"{field} = ${param_index}")
                values.append(value)
                param_index += 1
        
        if not set_parts:
            return  # Nothing to update
        
        query = f"""
            INSERT INTO server_config (guild_id, {', '.join(kwargs.keys())})
            VALUES ({', '.join([f'${i}' for i in range(1, len(values)+1)])})
            ON CONFLICT (guild_id) DO UPDATE SET
                {', '.join(set_parts)}, updated_at = NOW()
        """
        
        await self.execute(query, *values)