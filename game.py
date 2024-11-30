games = {}

def get_feedback(secret_word, guess):
    """Function to provide feedback for a guess"""
    # Normalize 'Ё' to 'Е' in both secret word and guess
    secret_word = secret_word.replace('ё', 'е').replace('Ё', 'Е')
    guess = guess.replace('ё', 'е').replace('Ё', 'Е')
    
    feedback = ""
    result = ""
    correct_letters = set()
    used_letters = set()
    
    # Create a list to track used positions for yellow marks
    secret_chars = list(secret_word)
    marked_positions = set()

    # First pass - mark green squares
    for i, (s_char, g_char) in enumerate(zip(secret_word, guess)):
        if g_char == s_char:
            feedback += "🟩"
            result += g_char.upper()
            correct_letters.add(g_char.upper())
            marked_positions.add(i)
            secret_chars[i] = None  # Mark as used
        else:
            feedback += " "  # Placeholder
            result += " "   # Placeholder

    # Second pass - mark yellow and white squares
    for i, g_char in enumerate(guess):
        if i in marked_positions:
            continue
            
        g_char_upper = g_char.upper()
        result = result[:i] + g_char_upper + result[i+1:]
        
        if g_char in secret_chars:
            feedback = feedback[:i] + "🟨" + feedback[i+1:]
            correct_letters.add(g_char_upper)
            secret_chars.remove(g_char)  # Remove first occurrence
        else:
            feedback = feedback[:i] + "⬜" + feedback[i+1:]
            used_letters.add(g_char_upper)
            
    return result, feedback, correct_letters, used_letters

def create_game(word_setter_username, second_player_username, word_setter_chat_id, guesser_chat_id):
    """Create a new game"""
    games[(word_setter_username, second_player_username)] = {
        'state': 'waiting_for_word',
        'secret_word': '',
        'attempts': [],
        'word_setter_chat_id': word_setter_chat_id,
        'guesser_chat_id': guesser_chat_id,
        'word_setter_username': word_setter_username,
        'guesser_username': second_player_username,
        'max_attempts': 6
    }

def get_game(word_setter_username, guesser_username):
    """Get game by usernames"""
    return games.get((word_setter_username, guesser_username))

def delete_game(word_setter_username, guesser_username):
    """Delete game"""
    if (word_setter_username, guesser_username) in games:
        del games[(word_setter_username, guesser_username)]
