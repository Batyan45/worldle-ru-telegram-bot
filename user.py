import json

user_chat_ids = {}

def load_user_chat_ids():
    """Load user chat IDs from a file."""
    try:
        with open('user_chat_ids.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_chat_ids():
    """Save user chat IDs to a file."""
    with open('user_chat_ids.json', 'w') as file:
        json.dump(user_chat_ids, file)

user_chat_ids = load_user_chat_ids()
