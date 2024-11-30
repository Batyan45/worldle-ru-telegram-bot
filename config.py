import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
