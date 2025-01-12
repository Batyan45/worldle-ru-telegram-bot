"""Start command handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from src.core.user import update_user_data
from src.config.strings import START_MESSAGE, NO_USERNAME_MESSAGE


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
    """
    user = update.message.from_user
    username = user.username
    chat_id = update.message.chat_id

    # Add logging
    logging.info(f"Start command received - Username: {username}, Chat ID: {chat_id}")

    # Check for username
    if not username:
        logging.warning("User without username tried to start bot")
        await update.message.reply_text(
            NO_USERNAME_MESSAGE,
            parse_mode='Markdown'
        )
        return

    # Save user's chat_id
    update_user_data(username, chat_id)
    
    try:
        await update.message.reply_text(
            START_MESSAGE,
            parse_mode='HTML'
        )
        logging.info(f"Start message sent successfully to {username}")
    except Exception as e:
        logging.error(f"Error sending start message: {str(e)}")
        await update.message.reply_text(
            START_MESSAGE,
            parse_mode=None
        )
        raise 