# Project Structure

```
telegram-bot/
├── src/                        # Source code directory
│   ├── bot/                    # Bot-related code
│   │   ├── handlers/          # Command and message handlers
│   │   │   ├── __init__.py
│   │   │   ├── addtry.py     # Add try command handler
│   │   │   ├── game.py       # Game-related command handlers
│   │   │   ├── guess.py      # Guess handling functionality
│   │   │   ├── say.py        # Say command handler
│   │   │   └── start.py      # Start command handler
│   │   ├── keyboards/         # Keyboard layouts
│   │   │   ├── __init__.py
│   │   │   └── inline.py     # Inline keyboard definitions
│   │   ├── __init__.py
│   │   └── commands.py       # Bot command definitions
│   ├── config/               # Configuration files
│   │   ├── __init__.py
│   │   ├── settings.py      # Application settings
│   │   └── strings.py       # Message strings and constants
│   ├── core/                # Core business logic
│   │   ├── __init__.py
│   │   ├── game.py         # Game logic and state management
│   │   └── user.py         # User management and persistence
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   └── logger.py       # Logging configuration
│   └── __init__.py
├── tests/                  # Test directory
├── gif/                    # GIF files for game responses
├── .env                    # Environment variables (not in VCS)
├── .env.example           # Example environment variables
├── .gitignore
├── run.py                 # Run the bot
├── Dockerfile
├── README.md
├── PROJECTMAP.md          # This file
├── docker-compose.yml
├── game_logs.log          # Game logs (not in VCS)
├── requirements.txt       # Python dependencies
└── user_data.json         # User data storage (not in VCS)
```

## Directory Structure Explanation

### `/src`
Main source code directory containing all application code.

#### `/src/bot`
Contains all Telegram bot-related code.
- `/handlers`: Command and message handlers for the bot
- `/keyboards`: Keyboard layout definitions
- `commands.py`: Bot command definitions and descriptions

#### `/src/config`
Configuration and constants.
- `settings.py`: Application settings and environment variables
- `strings.py`: Message strings and text constants

#### `/src/core`
Core business logic of the application.
- `game.py`: Game logic, state management, and game operations
- `user.py`: User data management and persistence

#### `/src/utils`
Utility functions and helpers.
- `logger.py`: Logging configuration and setup

### Root Directory Files
- `.env`: Environment variables (not in version control)
- `.env.example`: Example environment variables for setup
- `Dockerfile`: Docker container definition
- `docker-compose.yml`: Docker Compose configuration
- `requirements.txt`: Python package dependencies
- `game_logs.log`: Game activity logs (not in version control)
- `user_data.json`: User data storage (not in version control)

## Key Components

### Game Logic
The core game logic is implemented in `src/core/game.py`, which handles:
- Game state management
- Word validation and feedback
- Game creation and deletion

### Bot Handlers
Bot handlers in `src/bot/handlers/` manage different aspects of the game:
- `start.py`: Initial bot interaction
- `game.py`: Game flow and management
- `guess.py`: Word guessing logic
- `say.py`: In-game communication
- `addtry.py`: Additional attempts management

### Configuration
The application configuration is split between:
- Environment variables (`.env`)
- Application settings (`src/config/settings.py`)
- Message strings (`src/config/strings.py`)

### Data Persistence
User data is persisted using:
- `user_data.json` for user information
- `game_logs.log` for game activity logging 