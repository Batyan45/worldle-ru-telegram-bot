"""Say command handler for in-game communication."""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.core.game import games
from src.core.user import user_data
from src.config.strings import (
    NO_ACTIVE_GAME_MESSAGE_SAY,
    MESSAGE_RECEIVED,
    SAY_ENTER_MESSAGE,
    SAY_FAILED_TO_FIND_CHAT
)


# Conversation stages
SAY_WAITING_FOR_MESSAGE = 0


async def say_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /say command to send a message to another player.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    sender_username = update.effective_user.username
    message_text = ' '.join(context.args)

    # Delete the command message
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

    if message_text:
        # If text is provided with the command
        await send_say_message(update, context, message_text)
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id
            )
        except Exception as e:
            logging.warning(f"Failed to delete message: {e}")
    else:
        # If text is not provided, wait for the next message
        await update.effective_message.reply_text(SAY_ENTER_MESSAGE)
        return SAY_WAITING_FOR_MESSAGE


async def receive_say_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receive a message to send to another player.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        
    Returns:
        int: The next conversation state.
    """
    message_text = update.effective_message.text
    # Delete technical messages
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id - 1
        )
    except Exception as e:
        logging.warning(f"Failed to delete message: {e}")

    await send_say_message(update, context, message_text)
    return ConversationHandler.END


async def send_say_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str) -> None:
    """
    Send a message from one player to another.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
        message_text: The text message to send.
    """
    sender_username = update.effective_user.username
    # Find an active game involving the user
    game = next(
        (g for (w_s_username, g_username), g in games.items()
         if (w_s_username == sender_username or g_username == sender_username)
         and g.state == 'waiting_for_guess'),
        None
    )

    if not game:
        await update.effective_message.reply_text(NO_ACTIVE_GAME_MESSAGE_SAY, parse_mode='Markdown')
        return

    if sender_username == game.word_setter_username:
        receiver_username = game.guesser_username
    else:
        receiver_username = game.word_setter_username
    receiver_chat_id = user_data.get(receiver_username, {}).get('chat_id')

    if not receiver_chat_id:
        await update.effective_message.reply_text(SAY_FAILED_TO_FIND_CHAT, parse_mode='Markdown')
        return

    sender_chat_id = update.effective_chat.id

    # Send the message to both players
    for chat_id in [receiver_chat_id, sender_chat_id]:
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_RECEIVED.format(sender_username=f"_{sender_username}_", message_text=message_text),
            parse_mode='Markdown'
        ) 