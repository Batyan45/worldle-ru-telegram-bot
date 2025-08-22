"""Application configuration settings."""

import os
from pathlib import Path
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token
TELEGRAM_BOT_TOKEN: Final[str] = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Paths
BASE_DIR: Final[Path] = Path(__file__).resolve().parents[2]

DATA_DIR: Final[Path] = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
LOGS_DIR: Final[Path] = Path(os.getenv('LOGS_DIR', DATA_DIR / 'logs'))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_FILE: Final[Path] = Path(os.getenv('USER_DATA_FILE', DATA_DIR / 'user_data.json'))
GAME_LOGS_FILE: Final[Path] = Path(os.getenv('GAME_LOGS_FILE', LOGS_DIR / 'game_logs.log'))

GIFS_DIR: Final[Path] = Path(os.getenv('GIFS_DIR', BASE_DIR / 'gif'))

# Game settings
MAX_ATTEMPTS: Final[int] = int(os.getenv('MAX_ATTEMPTS', 6))
MIN_WORD_LENGTH: Final[int] = int(os.getenv('MIN_WORD_LENGTH', 4))
MAX_WORD_LENGTH: Final[int] = int(os.getenv('MAX_WORD_LENGTH', 8))

# Alphabets
RUSSIAN_ALPHABET: Final[set[str]] = set('АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
ENGLISH_ALPHABET: Final[set[str]] = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
