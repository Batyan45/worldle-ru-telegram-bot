import json
from strings import (
    SECOND_PLAYER_NOT_STARTED_MESSAGE,
    SECOND_PLAYER_HAS_ACTIVE_GAME_MESSAGE,
    WORD_PROMPT_MESSAGE,
    SECOND_PLAYER_WAITING_MESSAGE,
    INVALID_WORD_MESSAGE,
    WORD_SET_MESSAGE,
    GUESS_PROMPT_MESSAGE,
    NO_ACTIVE_GAME_MESSAGE,
    INVALID_GUESS_MESSAGE,
    ATTEMPT_MESSAGE,
    GUESSER_WIN_MESSAGE,
    WORD_SETTER_WIN_MESSAGE,
    OUT_OF_ATTEMPTS_MESSAGE,
    WORD_SETTER_LOSS_MESSAGE,
    TRY_AGAIN_MESSAGE,
)

games = {}

def get_feedback(secret_word, guess):
    """Функция для предоставления обратной связи по догадке"""
    # Normalize 'Ё' to 'Е' in both secret word and guess
    secret_word = secret_word.replace('ё', 'е')
    guess = guess.replace('ё', 'е')
    
    feedback = ""
    result = ""
    correct_letters = set()
    used_letters = set()
    for s_char, g_char in zip(secret_word, guess):
        g_char_upper = g_char.upper()
        if g_char == s_char:
            feedback += f"🟩"
            correct_letters.add(g_char_upper)
        elif g_char in secret_word:
            feedback += f"🟨"
            correct_letters.add(g_char_upper)
        else:
            feedback += f"⬜"
            used_letters.add(g_char_upper)
        result += g_char_upper
    return result, feedback, correct_letters, used_letters

def create_game(word_setter_username, second_player_username, word_setter_chat_id, guesser_chat_id):
    """Создание новой игры"""
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
    """Получение игры по именам пользователей"""
    return games.get((word_setter_username, guesser_username))

def delete_game(word_setter_username, guesser_username):
    """Удаление игры"""
    if (word_setter_username, guesser_username) in games:
        del games[(word_setter_username, guesser_username)]
