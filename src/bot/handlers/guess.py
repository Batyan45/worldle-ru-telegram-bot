"""Guess handling functionality."""

import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import telegram

from src.core.game import get_feedback, games, delete_game
from src.core.user import user_data, update_user_data
from src.config.settings import ENGLISH_ALPHABET, GIFS_DIR, RUSSIAN_ALPHABET
from src.config.strings import (
    NO_ACTIVE_GAME_MESSAGE,
    INVALID_GUESS_MESSAGE,
    INVALID_GUESS_LANGUAGE_MESSAGE,
    ATTEMPT_MESSAGE,
    GUESSER_WIN_MESSAGE,
    WORD_SETTER_WIN_MESSAGE,
    OUT_OF_ATTEMPTS_MESSAGE,
    WORD_SETTER_LOSS_MESSAGE,
    TRY_AGAIN_MESSAGE
)
from src.bot.handlers.game import get_random_gif
from src.bot.commands import update_user_commands


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle player's guesses.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
    """
    guesser_username = update.message.from_user.username
    message = update.message.text.strip().lower()

    # Find the corresponding game
    game = next(
        (g for (w_s_username, g_username), g in games.items()
         if g_username == guesser_username and g.state == 'waiting_for_guess'),
        None
    )
    word_setter_username = next(
        (w_s_username for (w_s_username, g_username), g in games.items()
         if g_username == guesser_username and g.state == 'waiting_for_guess'),
        None
    )

    if not game:
        await update.message.reply_text(NO_ACTIVE_GAME_MESSAGE, parse_mode='Markdown')
        return

    secret_word = game.secret_word

    if len(message) != len(secret_word) or not message.isalpha():
        await update.message.reply_text(
            INVALID_GUESS_MESSAGE.format(length=len(secret_word)),
            parse_mode='Markdown'
        )
        return

    # Check the language of the guess
    language = game.language
    if language == 'russian':
        # Normalize 'ё' to 'е' before checking
        normalized_message = message.replace('ё', 'е')
        if not all('а' <= c <= 'я' for c in normalized_message):
            await update.message.reply_text(INVALID_GUESS_LANGUAGE_MESSAGE, parse_mode='Markdown')
            return
    elif language == 'english':
        if not all('a' <= c <= 'z' for c in message):
            await update.message.reply_text(INVALID_GUESS_LANGUAGE_MESSAGE, parse_mode='Markdown')
            return

    # Add logging for the attempt
    logging.info(
        f"Guess attempt - Player: {guesser_username}, "
        f"Secret word: {secret_word}, "
        f"Guess: {message}, "
        f"Attempt #{len(game.attempts) + 1}"
    )

    result, feedback, correct_letters, used_letters = get_feedback(secret_word, message)
    game.attempts.append((result, feedback))

    # Update lists of used and correct letters without duplicates
    game.correct_letters.update(correct_letters - game.used_letters)
    game.used_letters.update(used_letters - game.correct_letters)

    attempt_number = len(game.attempts)

    # Form the message with the last attempt and number for the word setter
    attempt_text_setter = ATTEMPT_MESSAGE.format(
        attempt_number=attempt_number,
        max_attempts=game.max_attempts,
        result=result,
        feedback=feedback
    )

    try:
        await update.message.reply_text(attempt_text_setter, parse_mode='Markdown')
    except telegram.error.TimedOut:
        logging.warning("Timed out while sending attempt message, retrying...")
        try:
            await update.message.reply_text(attempt_text_setter, parse_mode='Markdown')
        except telegram.error.TimedOut:
            logging.error("Failed to send attempt message after retry")
            await update.message.reply_text("Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте еще раз.", parse_mode='Markdown')
            return

    # Form the message for the guesser with two columns
    attempts_text = "\n".join(
        f"`{attempt[0]}` | `{attempt[1]}`" for attempt in game.attempts
    )

    # Form the alphabet
    if language == 'russian':
        alphabet = RUSSIAN_ALPHABET
    else:
        alphabet = ENGLISH_ALPHABET
    correct_letters_display = " ".join(sorted(game.correct_letters))
    used_letters_display = " ".join(sorted(game.used_letters))
    remaining_letters = alphabet - game.correct_letters - game.used_letters
    remaining_letters_display = " ".join(sorted(remaining_letters))

    # Delete the previous message with attempts and alphabet if it exists
    if 'last_attempt_message' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data['last_attempt_message']
            )
        except Exception as e:
            logging.warning(f"Failed to delete message: {e}")

    # Send the new message to the guesser
    sent_message = await update.message.reply_text(
        f"{attempts_text}\n\n{remaining_letters_display}\n\n🟩🟨: {correct_letters_display}\n\n⬜: {used_letters_display}",
        parse_mode='Markdown'
    )

    # Save the ID of the last message with attempts and alphabet
    context.user_data['last_attempt_message'] = sent_message.message_id

    # Send the attempt to the word setter with a note
    word_setter_chat_id = game.word_setter_chat_id
    try:
        await context.bot.send_message(
            chat_id=word_setter_chat_id,
            text=ATTEMPT_MESSAGE.format(
                attempt_number=attempt_number,
                max_attempts=game.max_attempts,
                result=result,
                feedback=feedback
            ),
            parse_mode='Markdown'
        )
    except telegram.error.TimedOut:
        logging.warning("Timed out while sending message to word setter, retrying...")
        try:
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=ATTEMPT_MESSAGE.format(
                    attempt_number=attempt_number,
                    max_attempts=game.max_attempts,
                    result=result,
                    feedback=feedback
                ),
                parse_mode='Markdown'
            )
        except telegram.error.TimedOut:
            logging.error("Failed to send message to word setter after retry")

    if message.replace('ё', 'е').replace('Ё', 'Е') == secret_word.replace('ё', 'е').replace('Ё', 'Е'):
        # Log the successful completion of the game
        logging.info(
            f"Game won - Guesser: {guesser_username} won against {word_setter_username}, "
            f"Secret word: {secret_word}, "
            f"Attempts used: {attempt_number}/{game.max_attempts}"
        )

        try:
            # Send the message and GIF only to the guesser
            await update.message.reply_text(GUESSER_WIN_MESSAGE, parse_mode='Markdown')
            gif_path = get_random_gif(str(GIFS_DIR / 'win'))
            if gif_path:
                try:
                    with open(gif_path, 'rb') as gif:
                        await update.message.reply_animation(animation=gif)
                except Exception as e:
                    logging.error(f"Failed to send GIF: {e}")
        except telegram.error.TimedOut:
            logging.warning("Timed out while sending win message to guesser, retrying...")
            try:
                await update.message.reply_text(GUESSER_WIN_MESSAGE, parse_mode='Markdown')
            except telegram.error.TimedOut:
                logging.error("Failed to send win message to guesser after retry")

        try:
            # Send only the text message to the word setter
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=WORD_SETTER_WIN_MESSAGE.format(guesser_username=guesser_username),
                parse_mode='Markdown'
            )
        except telegram.error.TimedOut:
            logging.warning("Timed out while sending win message to word setter, retrying...")
            try:
                await context.bot.send_message(
                    chat_id=word_setter_chat_id,
                    text=WORD_SETTER_WIN_MESSAGE.format(guesser_username=guesser_username),
                    parse_mode='Markdown'
                )
            except telegram.error.TimedOut:
                logging.error("Failed to send win message to word setter after retry")
        # Delete the game
        delete_game(word_setter_username, guesser_username)

        # Update the last partner
        update_user_data(word_setter_username, word_setter_chat_id, guesser_username)
        update_user_data(guesser_username, update.message.chat_id, word_setter_username)

        # Update commands for both players
        await update_user_commands(update, context)
        # Create a fake update for the word setter to update their commands
        word_setter_update = Update(0)
        word_setter_update._effective_user = type('User', (), {'username': word_setter_username})()
        word_setter_update._effective_chat = type('Chat', (), {'id': word_setter_chat_id})()
        await update_user_commands(word_setter_update, context)
    else:
        if attempt_number >= game.max_attempts:
            # Log the loss
            logging.info(
                f"Game lost - Guesser: {guesser_username} lost against {word_setter_username}, "
                f"Secret word: {secret_word}, "
                f"All {game.max_attempts} attempts used"
            )

            await update.message.reply_text(
                OUT_OF_ATTEMPTS_MESSAGE.format(secret_word=secret_word.upper()),
                parse_mode='Markdown'
            )
            # Inform the word setter
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=WORD_SETTER_LOSS_MESSAGE.format(guesser_username=guesser_username),
                parse_mode='Markdown'
            )
            # Delete the game
            delete_game(word_setter_username, guesser_username)

            # Update the last partner
            update_user_data(word_setter_username, word_setter_chat_id, guesser_username)
            update_user_data(guesser_username, update.message.chat_id, word_setter_username)

            # Update commands for both players
            await update_user_commands(update, context)
            # Create a fake update for the word setter to update their commands
            word_setter_update = Update(0)
            word_setter_update._effective_user = type('User', (), {'username': word_setter_username})()
            word_setter_update._effective_chat = type('Chat', (), {'id': word_setter_chat_id})()
            await update_user_commands(word_setter_update, context)
        else:
            remaining_attempts = game.max_attempts - attempt_number
            await update.message.reply_text(
                TRY_AGAIN_MESSAGE.format(remaining_attempts=remaining_attempts),
                parse_mode='Markdown'
            ) 