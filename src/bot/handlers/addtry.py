"""Add try command handler."""

from telegram import Update
from telegram.ext import ContextTypes

from src.core.game import games
from src.config.strings import (
    NO_ACTIVE_GAME_MESSAGE,
    ADDTRY_ADDED_MESSAGE,
    ADDTRY_RECEIVED_MESSAGE
)


async def addtry_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /addtry command to add one attempt to the guessing player.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
    """
    word_setter_username = update.message.from_user.username
    # Find the current game for the word setter
    game = next(
        (g for (w_s_username, g_username), g in games.items()
         if w_s_username == word_setter_username and g.state == 'waiting_for_guess'),
        None
    )
    if not game:
        await update.message.reply_text(NO_ACTIVE_GAME_MESSAGE, parse_mode='Markdown')
        return

    game.max_attempts += 1
    await update.message.reply_text(ADDTRY_ADDED_MESSAGE, parse_mode='Markdown')

    # Notify the guessing player
    guesser_chat_id = game.guesser_chat_id
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text=ADDTRY_RECEIVED_MESSAGE,
        parse_mode='Markdown'
    )