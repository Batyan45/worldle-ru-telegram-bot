"""Application configuration settings."""

import os
from pathlib import Path
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token
TELEGRAM_BOT_TOKEN: Final[str] = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Game settings
MAX_ATTEMPTS: Final[int] = 6
MIN_WORD_LENGTH: Final[int] = 4
MAX_WORD_LENGTH: Final[int] = 8

# Paths
BASE_DIR: Final[Path] = Path(__file__).parent.parent.parent
GIFS_DIR: Final[Path] = BASE_DIR / 'gif'
USER_DATA_FILE: Final[Path] = BASE_DIR / 'user_data.json'
GAME_LOGS_FILE: Final[Path] = BASE_DIR / 'game_logs.log'

# Alphabets
RUSSIAN_ALPHABET: Final[set[str]] = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
ENGLISH_ALPHABET: Final[set[str]] = set('abcdefghijklmnopqrstuvwxyz') 