# main.py

import logging
import asyncio
import nest_asyncio
from telegram import Update
from config import TELEGRAM_BOT_TOKEN
from strings import (
    START_MESSAGE,
    NO_USERNAME_MESSAGE,
    NEW_GAME_MESSAGE,
    NO_USERNAME_NEW_GAME_MESSAGE,
    SECOND_PLAYER_NOT_STARTED_MESSAGE,
    SECOND_PLAYER_WAITING_MESSAGE,
    SECOND_PLAYER_HAS_ACTIVE_GAME_MESSAGE,
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
    ERROR_MESSAGE,
    START_COMMAND_DESCRIPTION,
    NEW_GAME_COMMAND_DESCRIPTION,
    CANCEL_COMMAND_DESCRIPTION,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
from game import (
    create_game,
    get_game,
    delete_game,
    get_feedback,
    games
)
from user import (
    user_chat_ids,
    save_user_chat_ids
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Этапы разговора
WAITING_FOR_SECOND_PLAYER, WAITING_FOR_WORD = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.message.from_user
    username = user.username
    chat_id = update.message.chat_id
    # Сохраняем chat_id пользователя
    word_setter_username = username
    second_player_username = context.user_data.get('guesser_username', None)
    if username and second_player_username:
        user_chat_ids[username] = chat_id
        await update.message.reply_text(
            START_MESSAGE
        )
        if (second_player_username, word_setter_username) in games:
            await update.message.reply_text(
                SECOND_PLAYER_HAS_ACTIVE_GAME_MESSAGE.format(second_player=second_player_username)
            )
            return WAITING_FOR_SECOND_PLAYER
        save_user_chat_ids()
        await update.message.reply_text(
            NO_USERNAME_MESSAGE
        )


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new_game для начала новой игры"""
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text(NO_USERNAME_NEW_GAME_MESSAGE)
        return ConversationHandler.END

    await update.message.reply_text(NEW_GAME_MESSAGE)
    return WAITING_FOR_SECOND_PLAYER


async def set_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка второго игрока"""
    second_player = update.message.text.strip()
    if not second_player.startswith('@'):
        second_player = '@' + second_player  # Добавляем '@' в начало
    second_player_username = second_player[1:]  # Убираем '@'

    word_setter_username = update.message.from_user.username
    if second_player_username not in user_chat_ids or get_game(word_setter_username, second_player_username):
        await update.message.reply_text(
            SECOND_PLAYER_NOT_STARTED_MESSAGE.format(second_player=second_player)
        )
        return WAITING_FOR_SECOND_PLAYER

    word_setter_username = update.message.from_user.username
    word_setter_chat_id = update.message.chat_id
    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = second_player_username

    guesser_chat_id = user_chat_ids[second_player_username]

    # Создаём новую игру
    create_game(word_setter_username, second_player_username, word_setter_chat_id, guesser_chat_id)

    await update.message.reply_text(
        WORD_PROMPT_MESSAGE.format(word_setter_username=word_setter_username)
    )
    # Notify the second player that the first player is setting a word
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text=SECOND_PLAYER_WAITING_MESSAGE.format(word_setter_username=word_setter_username)
    )
    return WAITING_FOR_WORD


async def receive_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение загаданного слова и начало игры"""
    word = update.message.text.strip().lower()
    if len(word) != 5 or not word.isalpha():
        await update.message.reply_text(INVALID_WORD_MESSAGE)
        return WAITING_FOR_WORD

    word_setter_username = context.user_data['word_setter_username']
    guesser_username = context.user_data['guesser_username']
    game = get_game(word_setter_username, guesser_username)

    if game and game['state'] == 'waiting_for_word':
        game['secret_word'] = word
        game['state'] = 'waiting_for_guess'
        await update.message.reply_text(WORD_SET_MESSAGE)

        # Отправляем сообщение угадывающему
        guesser_chat_id = game['guesser_chat_id']
        await context.bot.send_message(
            chat_id=guesser_chat_id,
            text=GUESS_PROMPT_MESSAGE.format(word_setter_username=word_setter_username)
        )
        save_user_chat_ids()
        return ConversationHandler.END

async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка догадок игрока"""
    guesser_username = update.message.from_user.username
    message = update.message.text.strip().lower()
    if len(message) != 5 or not message.isalpha():
        await update.message.reply_text(INVALID_GUESS_MESSAGE)
        return

    # Поиск соответствующей игры
    game = next(
        (g for (w_s_username, g_username), g in games.items() if g_username == guesser_username and g['state'] == 'waiting_for_guess'),
        None
    )
    word_setter_username = next(
        (w_s_username for (w_s_username, g_username), g in games.items() if g_username == guesser_username and g['state'] == 'waiting_for_guess'),
        None
    )

    if not game:
        await update.message.reply_text(NO_ACTIVE_GAME_MESSAGE)
        return

    secret_word = game['secret_word']
    result, feedback = get_feedback(secret_word, message)
    game['attempts'].append((result, feedback))

    attempt_number = len(game['attempts'])

    # Формируем сообщение с последней попыткой и номером
    attempt_text = ATTEMPT_MESSAGE.format(
        attempt_number=attempt_number, result=result, feedback=feedback
    )

    await update.message.reply_text(attempt_text)

    # Отправляем попытку загадавшему игроку с припиской
    word_setter_chat_id = game['word_setter_chat_id']
    await context.bot.send_message(
        chat_id=word_setter_chat_id,
        text=ATTEMPT_MESSAGE.format(
            attempt_number=attempt_number, result=result, feedback=feedback
        )
    )

    if message == secret_word:
        await update.message.reply_text(GUESSER_WIN_MESSAGE)

        # Отправляем сообщение загадывающему
        await context.bot.send_message(
            chat_id=word_setter_chat_id,
            text=WORD_SETTER_WIN_MESSAGE.format(guesser_username=guesser_username)
        )

        # Удаляем игру
        delete_game(word_setter_username, guesser_username)
    else:
        if attempt_number >= 6:
            await update.message.reply_text(
                OUT_OF_ATTEMPTS_MESSAGE.format(secret_word=secret_word.upper())
            )
            # Информируем загадавшего игрока
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=WORD_SETTER_LOSS_MESSAGE.format(guesser_username=guesser_username)
            )
            # Удаляем игру
            del games[(word_setter_username, guesser_username)]
        else:
            remaining_attempts = 6 - attempt_number
            await update.message.reply_text(
                TRY_AGAIN_MESSAGE.format(remaining_attempts=remaining_attempts)
            )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена игры"""
    await update.message.reply_text(CANCEL_MESSAGE)
    return ConversationHandler.END

async def main():
    """Основная функция запуска бота"""
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_game', new_game)],
        states={
            WAITING_FOR_SECOND_PLAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_player)],
            WAITING_FOR_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_word)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    # Обработчик догадок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_word))

    # Set bot commands for the command hints
    await application.bot.set_my_commands([
        ("start", START_COMMAND_DESCRIPTION),
        ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
        ("cancel", CANCEL_COMMAND_DESCRIPTION)
    ])

    await application.run_polling()


if __name__ == '__main__':
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    finally:
        save_user_chat_ids()
