"""Game-related command handlers."""

import logging
import random
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.core.game import (
    create_game,
    get_game,
    delete_game,
    get_feedback,
    games
)
from src.core.user import user_data, update_user_data
from src.config.settings import GIFS_DIR
from src.config.strings import (
    NEW_GAME_MESSAGE,
    NO_USERNAME_NEW_GAME_MESSAGE,
    SECOND_PLAYER_NOT_STARTED_MESSAGE,
    SECOND_PLAYER_WAITING_MESSAGE,
    WORD_PROMPT_MESSAGE,
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
    CANCEL_MESSAGE,
    MIXED_LANGUAGE_MESSAGE,
    INVALID_GUESS_LANGUAGE_MESSAGE,
    LANGUAGE_STRINGS
)
from src.bot.keyboards.inline import create_last_partner_keyboard


# Conversation stages
WAITING_FOR_SECOND_PLAYER, WAITING_FOR_WORD = range(2)


def get_random_gif(directory: str) -> str | None:
    """
    Get a random GIF file from the specified directory.
    
    Args:
        directory: Path to the directory containing GIFs.
        
    Returns:
        str | None: Path to the random GIF file or None if no GIFs found.
    """
    try:
        gif_files = list(Path(directory).glob('*.gif'))
        if gif_files:
            return str(random.choice(gif_files))
        return None
    except Exception as e:
        logging.error(f"Error getting random GIF: {e}")
        return None


async def new_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /new_game command.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text(NO_USERNAME_NEW_GAME_MESSAGE, parse_mode='Markdown')
        return ConversationHandler.END

    last_partner = user_data.get(username, {}).get('last_partner')
    if last_partner:
        keyboard = create_last_partner_keyboard(last_partner)
        await update.message.reply_text(NEW_GAME_MESSAGE, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(NEW_GAME_MESSAGE, parse_mode='Markdown')
    return WAITING_FOR_SECOND_PLAYER


async def set_player(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle setting the second player for a new game.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    second_player = update.message.text.strip()
    if not second_player.startswith('@'):
        second_player = '@' + second_player
    second_player_username = second_player[1:]

    word_setter_username = update.message.from_user.username
    if second_player_username not in user_data or get_game(word_setter_username, second_player_username):
        await update.message.reply_text(
            SECOND_PLAYER_NOT_STARTED_MESSAGE.format(second_player=second_player),
            parse_mode='Markdown'
        )
        return WAITING_FOR_SECOND_PLAYER

    word_setter_chat_id = update.message.chat_id
    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = second_player_username

    # Save the last partner for each user
    update_user_data(word_setter_username, word_setter_chat_id, second_player_username)
    guesser_chat_id = user_data[second_player_username]['chat_id']
    update_user_data(second_player_username, guesser_chat_id, word_setter_username)

    # Create a new game
    create_game(word_setter_username, second_player_username, word_setter_chat_id, guesser_chat_id)

    await update.message.reply_text(
        WORD_PROMPT_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )
    # Notify the second player that the first player is setting a word
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text=SECOND_PLAYER_WAITING_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )
    return WAITING_FOR_WORD


async def receive_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle receiving the secret word from the word setter.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    word = update.message.text.strip().lower()
    if len(word) not in range(4, 9) or not word.isalpha():
        await update.message.reply_text(INVALID_WORD_MESSAGE, parse_mode='Markdown')
        return WAITING_FOR_WORD

    word_setter_username = context.user_data['word_setter_username']
    guesser_username = context.user_data['guesser_username']
    game = get_game(word_setter_username, guesser_username)

    # Determine the language
    if all('а' <= c <= 'я' or c == 'ё' for c in word):
        game.language = 'russian'
    elif all('a' <= c <= 'z' for c in word):
        game.language = 'english'
    else:
        await update.message.reply_text(MIXED_LANGUAGE_MESSAGE, parse_mode='Markdown')
        return WAITING_FOR_WORD

    if game and game.state == 'waiting_for_word':
        game.secret_word = word
        game.state = 'waiting_for_guess'
        
        # Log the start of the game
        logging.info(
            f"Game started - Word setter: {word_setter_username}, "
            f"Guesser: {guesser_username}, "
            f"Secret word: {word}, "
            f"Language: {game.language}"
        )

        await update.message.reply_text(WORD_SET_MESSAGE, parse_mode='Markdown')

        # Send message to the guesser
        language_str = LANGUAGE_STRINGS[game.language]
        await context.bot.send_message(
            chat_id=game.guesser_chat_id,
            text=GUESS_PROMPT_MESSAGE.format(
                word_setter_username=word_setter_username,
                language=language_str,
                length=len(word)
            ),
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /cancel command.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    username = update.effective_user.username
    # Find and delete the active game involving the user
    game_key = next(
        ((w_s_username, g_username) for (w_s_username, g_username) in games
         if w_s_username == username or g_username == username),
        None
    )
    if game_key:
        del games[game_key]
        await update.effective_message.reply_text(CANCEL_MESSAGE, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(NO_ACTIVE_GAME_MESSAGE, parse_mode='Markdown')
    return ConversationHandler.END


async def handle_last_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle clicking on the button with the last partner.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    query = update.callback_query
    await query.answer()
    last_partner_username = query.data.replace('last_partner_', '')
    word_setter_username = update.effective_user.username

    # Check if the last partner has started the bot
    if last_partner_username not in user_data:
        await query.message.reply_text(
            SECOND_PLAYER_NOT_STARTED_MESSAGE.format(second_player=f"@{last_partner_username}"),
            parse_mode='Markdown'
        )
        return WAITING_FOR_SECOND_PLAYER

    # Check if there's already an active game
    if get_game(word_setter_username, last_partner_username):
        await query.message.reply_text(
            SECOND_PLAYER_NOT_STARTED_MESSAGE.format(second_player=f"@{last_partner_username}"),
            parse_mode='Markdown'
        )
        return WAITING_FOR_SECOND_PLAYER

    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = last_partner_username

    # Create a new game
    word_setter_chat_id = user_data[word_setter_username]['chat_id']
    guesser_chat_id = user_data[last_partner_username]['chat_id']
    
    # Create a new game
    create_game(word_setter_username, last_partner_username, word_setter_chat_id, guesser_chat_id)

    # Save the last partner for each user
    update_user_data(word_setter_username, word_setter_chat_id, last_partner_username)
    update_user_data(last_partner_username, guesser_chat_id, word_setter_username)

    # Send messages to both players
    await query.message.reply_text(
        WORD_PROMPT_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text=SECOND_PLAYER_WAITING_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_WORD 