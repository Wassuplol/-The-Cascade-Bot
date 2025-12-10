# The Cascade Bot

An enterprise-grade Discord bot built with Python and Discord.py v2.3+ featuring comprehensive moderation, logging, fun, and utility systems.

## Features

- **Moderation System**: Advanced warning, mute, kick, and ban commands with logging
- **Logging System**: Comprehensive message and user activity logging
- **Fun Commands**: Entertainment features like dice rolling, coin flipping, and more
- **Utility Commands**: Information commands, server stats, and bot information
- **Database Integration**: PostgreSQL for persistent data storage
- **Caching**: Redis for high-performance caching
- **Security**: Rate limiting, permission checks, and input sanitization

## Requirements

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Discord Bot Token

## Installation

### Quick Start with Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd TheCascadeBot
```

2. Create a `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env with your bot token and other settings
```

3. Start the bot with Docker Compose:
```bash
docker-compose up -d
```

### Manual Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database and Redis server

3. Create a `.env` file with your configuration:
```bash
DISCORD_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/thecascade
REDIS_URL=redis://localhost:6379
```

4. Run the bot:
```bash
python bot.py
```

## Configuration

### Environment Variables

- `DISCORD_TOKEN`: Your Discord bot token
- `COMMAND_PREFIX`: Command prefix (default: `!`)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SPAM_THRESHOLD_MESSAGES`: Number of messages for spam detection
- `SPAM_THRESHOLD_SECONDS`: Time window for spam detection
- `TOXICITY_THRESHOLD`: Threshold for toxicity detection (0.0-1.0)

## Commands

### Moderation Commands
- `!warn @user [reason]` - Warn a user
- `!mute @user [duration] [reason]` - Mute a user
- `!kick @user [reason]` - Kick a user
- `!ban @user [reason]` - Ban a user
- `!infractions [@user]` - View user's infraction history

### Logging Commands
- `!setlogchannel [#channel]` - Set the logging channel
- `!messagelog [message_id]` - View logged message details

### Fun Commands
- `!ping` - Check bot latency
- `!roll [dice]` - Roll virtual dice (e.g., 2d6, 1d20)
- `!choose [option1] [option2] ...` - Choose randomly from options
- `!coinflip` - Flip a coin
- `!avatar [@user]` - Get user's avatar

### Utility Commands
- `!serverinfo` - Get server information
- `!userinfo [@user]` - Get user information
- `!botinfo` - Get bot information
- `!stats` - Get detailed bot statistics
- `!help` - Show help information

## Architecture

The bot follows a modular architecture with the following core components:

- **Core**: Core bot functionality, database management, caching, logging
- **Cogs**: Modular command groups (Moderation, Logging, Fun, Utility)
- **Configuration**: Environment-based configuration management
- **Database**: PostgreSQL integration for persistent storage
- **Cache**: Redis integration for high-performance caching

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.