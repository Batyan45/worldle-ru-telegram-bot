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
    feedback = ""
    result = ""
    for s_char, g_char in zip(secret_word, guess):
        if g_char == s_char:
            feedback += f"🟩"
        elif g_char in secret_word:
            feedback += f"🟨"
        else:
            feedback += f"⬜"
        result += g_char.upper()
    return result, feedback

def create_game(word_setter_username, second_player_username, word_setter_chat_id, guesser_chat_id):
    """Создание новой игры"""
    games[(word_setter_username, second_player_username)] = {
        'state': 'waiting_for_word',
        'secret_word': '',
        'attempts': [],
        'word_setter_chat_id': word_setter_chat_id,
        'guesser_chat_id': guesser_chat_id
    }

def get_game(word_setter_username, guesser_username):
    """Получение игры по именам пользователей"""
    return games.get((word_setter_username, guesser_username))

def delete_game(word_setter_username, guesser_username):
    """Удаление игры"""
    if (word_setter_username, guesser_username) in games:
        del games[(word_setter_username, guesser_username)]
