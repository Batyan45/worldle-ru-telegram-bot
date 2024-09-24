import json

user_data = {}

def load_user_data():
    """Load user data from a file."""
    try:
        with open('user_data.json', 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data():
    """Save user data to a file."""
    with open('user_data.json', 'w') as file:
        json.dump(user_data, file)

user_data = load_user_data()
