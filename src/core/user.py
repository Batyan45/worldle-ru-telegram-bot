"""User management and data persistence."""

import json
from typing import Dict, Any
from pathlib import Path

from src.config.settings import USER_DATA_FILE


# Global user state
user_data: Dict[str, Dict[str, Any]] = {}


def load_user_data() -> None:
    """Load user data from the JSON file."""
    try:
        if USER_DATA_FILE.exists():
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                global user_data
                user_data = json.load(f)
    except Exception as e:
        print(f"Error loading user data: {e}")
        user_data.clear()


def save_user_data() -> None:
    """Save user data to the JSON file."""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving user data: {e}")


def get_user_chat_id(username: str) -> int:
    """
    Get user's chat ID.
    
    Args:
        username: The username to look up.
        
    Returns:
        int: The user's chat ID if found, None otherwise.
    """
    return user_data.get(username, {}).get('chat_id')


def update_user_data(username: str, chat_id: int, last_partner: str = None) -> None:
    """
    Update user data.
    
    Args:
        username: The username to update.
        chat_id: The user's chat ID.
        last_partner: Optional username of the last game partner.
    """
    if username not in user_data:
        user_data[username] = {}
    
    user_data[username]['chat_id'] = chat_id
    if last_partner:
        user_data[username]['last_partner'] = last_partner
    
    save_user_data()


# Load user data on module import
load_user_data() 