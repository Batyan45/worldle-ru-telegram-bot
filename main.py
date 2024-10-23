# main.py

import logging
import asyncio
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommandScopeChat
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
    MIXED_LANGUAGE_MESSAGE,
    INVALID_GUESS_LANGUAGE_MESSAGE,
    ERROR_MESSAGE,
    START_COMMAND_DESCRIPTION,
    NEW_GAME_COMMAND_DESCRIPTION,
    CANCEL_COMMAND_DESCRIPTION,
    LANGUAGE_STRINGS,
    RUSSIAN_ALPHABET,
    ENGLISH_ALPHABET,
    SAY_COMMAND_DESCRIPTION,
    NO_ACTIVE_GAME_MESSAGE_SAY,
    MESSAGE_RECEIVED,
    ADDTRY_COMMAND_DESCRIPTION,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from game import (
    create_game,
    get_game,
    delete_game,
    get_feedback,
    games
)
from user import (
    user_data,
    save_user_data
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('game_logs.log'),
        logging.StreamHandler()
    ]
)

# Этапы разговора
WAITING_FOR_SECOND_PLAYER, WAITING_FOR_WORD, SAY_WAITING_FOR_MESSAGE = range(3)

# Обработчик нажатий на кнопки

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.message.from_user
    username = user.username
    chat_id = update.message.chat_id
    # Сохраняем chat_id пользователя
    word_setter_username = username
    if username:
        if username not in user_data:
            user_data[username] = {}
        user_data[username]['chat_id'] = chat_id
        await update.message.reply_text(
            START_MESSAGE,
            parse_mode='Markdown'
        )
        save_user_data()


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new_game для начала новой игры"""
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text(NO_USERNAME_NEW_GAME_MESSAGE, parse_mode='Markdown')
        return ConversationHandler.END

    last_partner = user_data.get(username, {}).get('last_partner')
    if last_partner:
        keyboard = [[InlineKeyboardButton(f"Играть с @{last_partner}", callback_data=f"last_partner_{last_partner}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(NEW_GAME_MESSAGE, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(NEW_GAME_MESSAGE, parse_mode='Markdown')
    return WAITING_FOR_SECOND_PLAYER


async def set_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка второго игрока"""
    second_player = update.message.text.strip()
    if not second_player.startswith('@'):
        second_player = '@' + second_player  # Добавляем '@' в начало
    second_player_username = second_player[1:]  # Убираем '@'

    word_setter_username = update.message.from_user.username
    if second_player_username not in user_data or get_game(word_setter_username, second_player_username):
        await update.message.reply_text(
            SECOND_PLAYER_NOT_STARTED_MESSAGE.format(second_player=second_player),
            parse_mode='Markdown'
        )
        return WAITING_FOR_SECOND_PLAYER

    word_setter_username = update.message.from_user.username
    word_setter_chat_id = update.message.chat_id
    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = second_player_username

    # Сохраняем последнего партнёра для каждого пользователя
    user_data[word_setter_username]['last_partner'] = second_player_username
    user_data[second_player_username]['last_partner'] = word_setter_username
    save_user_data()

    guesser_chat_id = user_data[second_player_username]['chat_id']

    # Создаём новую игру
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

async def say(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /say для отправки сообщения другому игроку."""
    sender_username = update.effective_user.username
    message_text = ' '.join(context.args)

    # Удаляем сообщение с командой
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение: {e}")

    if message_text:
        # Если текст передан вместе с командой
        await send_say_message(update, context, message_text)
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
        except Exception as e:
            logging.warning(f"Не удалось удалить сообщение: {e}")
    else:
        # Если текст не передан, ожидаем следующего сообщения
        await update.effective_message.reply_text("Введите сообщение, которое хотите отправить:")
        return SAY_WAITING_FOR_MESSAGE

async def receive_say_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение сообщения для отправки другому игроку."""
    message_text = update.effective_message.text
    # Удаляем технические сообщения
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id - 1)
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение: {e}")

    await send_say_message(update, context, message_text)
    return ConversationHandler.END

async def send_say_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text):
    """Отправка сообщения от одного игрока другому."""
    sender_username = update.effective_user.username
    # Поиск активной игры с участием пользователя
    game = next(
        (g for (w_s_username, g_username), g in games.items()
         if (w_s_username == sender_username or g_username == sender_username)
         and g['state'] == 'waiting_for_guess'),
        None
    )

    if not game:
        await update.effective_message.reply_text(NO_ACTIVE_GAME_MESSAGE_SAY, parse_mode='Markdown')
        return

    if sender_username == game['word_setter_username']:
        receiver_username = game['guesser_username']
    else:
        receiver_username = game['word_setter_username']
    receiver_chat_id = user_data.get(receiver_username, {}).get('chat_id')

    if not receiver_chat_id:
        await update.effective_message.reply_text("Не удалось найти чат другого игрока.", parse_mode='Markdown')
        return

    sender_chat_id = update.effective_chat.id

    # Отправляем сообщение обоим игрокам
    for chat_id in [receiver_chat_id, sender_chat_id]:
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_RECEIVED.format(sender_username=f"_{sender_username}_", message_text=message_text),
            parse_mode='Markdown'
        )



async def addtry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /addtry для добавления одной попытки угадывающему игроку."""
    word_setter_username = update.message.from_user.username
    # Найдём текущую игру для загадывающего игрока
    game = next(
        (g for (w_s_username, g_username), g in games.items()
         if w_s_username == word_setter_username and g['state'] == 'waiting_for_guess'),
        None
    )
    if not game:
        await update.message.reply_text("У вас нет активной игры, чтобы добавить попытку.", parse_mode='Markdown')
        return

    game['max_attempts'] += 1
    await update.message.reply_text("Вы добавили одну дополнительную попытку угадывающему игроку.", parse_mode='Markdown')

    # Уведомляем угадывающего игрока
    guesser_chat_id = game['guesser_chat_id']
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text="Загадывающий игрок добавил вам одну дополнительную попытку.",
        parse_mode='Markdown'
    )



async def receive_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение загаданного слова и начало игры"""
    word = update.message.text.strip().lower()
    if len(word) not in range(4, 9) or not word.isalpha():
        await update.message.reply_text(INVALID_WORD_MESSAGE, parse_mode='Markdown')
        return WAITING_FOR_WORD

    word_setter_username = context.user_data['word_setter_username']
    guesser_username = context.user_data['guesser_username']
    game = get_game(word_setter_username, guesser_username)

    # Определяем язык
    if all('а' <= c <= 'я' or c == 'ё' for c in word):
        game['language'] = 'russian'
    elif all('a' <= c <= 'z' for c in word):
        game['language'] = 'english'
    else:
        await update.message.reply_text(MIXED_LANGUAGE_MESSAGE, parse_mode='Markdown')
        return WAITING_FOR_WORD

    language_str = LANGUAGE_STRINGS[game['language']]

    if game and game['state'] == 'waiting_for_word':
        game['secret_word'] = word
        game['state'] = 'waiting_for_guess'
        
        # Логируем начало игры
        logging.info(
            f"Game started - Word setter: {word_setter_username}, "
            f"Guesser: {guesser_username}, "
            f"Secret word: {word}, "
            f"Language: {game['language']}"
        )

        await update.message.reply_text(WORD_SET_MESSAGE, parse_mode='Markdown')

        # Обновляем команды для обоих игроков
        await context.bot.set_my_commands([
            ("start", START_COMMAND_DESCRIPTION),
            ("say", SAY_COMMAND_DESCRIPTION),
            ("cancel", CANCEL_COMMAND_DESCRIPTION),
            ("addtry", ADDTRY_COMMAND_DESCRIPTION)
        ], scope=BotCommandScopeChat(game['word_setter_chat_id']))

        await context.bot.set_my_commands([
            ("start", START_COMMAND_DESCRIPTION),
            ("say", SAY_COMMAND_DESCRIPTION),
            ("cancel", CANCEL_COMMAND_DESCRIPTION)
        ], scope=BotCommandScopeChat(game['guesser_chat_id']))

        # Save the length of the word
        length = len(word)

        # Send message to the guesser
        guesser_chat_id = game['guesser_chat_id']
        language_str = LANGUAGE_STRINGS[game['language']]
        await context.bot.send_message(
            chat_id=guesser_chat_id,
            text=GUESS_PROMPT_MESSAGE.format(
                word_setter_username=word_setter_username,
                language=language_str,
                length=length
            ),
            parse_mode='Markdown'
        )
        save_user_data()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей игры."""
    username = update.effective_user.username
    # Ищем и удаляем активную игру с участием пользователя
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

async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка догадок игрока"""
    guesser_username = update.message.from_user.username
    message = update.message.text.strip().lower()

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
        await update.message.reply_text(NO_ACTIVE_GAME_MESSAGE, parse_mode='Markdown')
        return

    secret_word = game['secret_word']

    if len(message) != len(secret_word) or not message.isalpha():
        await update.message.reply_text(
            INVALID_GUESS_MESSAGE.format(length=len(secret_word)),
            parse_mode='Markdown'
        )
        return
    # Проверяем язык догадки
    language = game.get('language', 'russian')
    if language == 'russian':
        if not all('а' <= c <= 'я' or c == 'ё' for c in message):
            await update.message.reply_text(INVALID_GUESS_LANGUAGE_MESSAGE, parse_mode='Markdown')
            return
    elif language == 'english':
        if not all('a' <= c <= 'z' for c in message):
            await update.message.reply_text(INVALID_GUESS_LANGUAGE_MESSAGE, parse_mode='Markdown')
            return

    # Добавляем логирование попытки
    logging.info(
        f"Guess attempt - Player: {guesser_username}, "
        f"Secret word: {secret_word}, "
        f"Guess: {message}, "
        f"Attempt #{len(game['attempts']) + 1}"
    )

    result, feedback, correct_letters, used_letters = get_feedback(secret_word, message)
    game['attempts'].append((result, feedback))

    # Обновляем списки использованных и правильных букв без повторений
    if 'correct_letters' not in game:
        game['correct_letters'] = set()
    if 'used_letters' not in game:
        game['used_letters'] = set()
    game['correct_letters'].update(correct_letters - game['used_letters'])
    game['used_letters'].update(used_letters - game['correct_letters'])

    attempt_number = len(game['attempts'])

    # Формируем сообщение с последней попыткой и номером для загадавшего
    attempt_text_setter = ATTEMPT_MESSAGE.format(
        attempt_number=attempt_number,
        max_attempts=game['max_attempts'],
        result=result,
        feedback=feedback
    )

    await update.message.reply_text(attempt_text_setter, parse_mode='Markdown')

    # Формируем сообщение для угадывающего с двумя столбцами
    attempts_text = "\n".join(
        f"`{attempt[0]}` | `{attempt[1]}`" for attempt in game['attempts']
    )

    # Формируем алфавит
    if language == 'russian':
        alphabet = RUSSIAN_ALPHABET
    else:
        alphabet = ENGLISH_ALPHABET
    correct_letters_display = " ".join(sorted(game['correct_letters']))
    used_letters_display = " ".join(sorted(game['used_letters']))
    remaining_letters = alphabet - game['correct_letters'] - game['used_letters']
    remaining_letters_display = " ".join(sorted(remaining_letters))

    # Удаляем предыдущее сообщение с попытками и алфавитом, если оно существует
    if 'last_attempt_message' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data['last_attempt_message']
            )
        except Exception as e:
            logging.warning(f"Failed to delete message: {e}")

    # Отправляем новое сообщение угадывающему
    sent_message = await update.message.reply_text(
        f"{attempts_text}\n\n{remaining_letters_display}\n\n🟩🟨: {correct_letters_display}\n\n⬜: {used_letters_display}",
        parse_mode='Markdown'
    )

    # Сохраняем ID последнего сообщения с попытками и алфавитом
    context.user_data['last_attempt_message'] = sent_message.message_id

    # Отправляем попытку загада��шему игроку с припиской
    word_setter_chat_id = game['word_setter_chat_id']
    await context.bot.send_message(
        chat_id=word_setter_chat_id,
        text=ATTEMPT_MESSAGE.format(
            attempt_number=attempt_number,
            max_attempts=game['max_attempts'],
            result=result,
            feedback=feedback
        ),
        parse_mode='Markdown'
    )

    if message == secret_word:
        # Логируем успешное завершение игры
        logging.info(
            f"Game won - Guesser: {guesser_username} won against {word_setter_username}, "
            f"Secret word: {secret_word}, "
            f"Attempts used: {attempt_number}/{game['max_attempts']}"
        )

        await update.message.reply_text(GUESSER_WIN_MESSAGE, parse_mode='Markdown')

        # Отправляем сообщение загадывающему
        await context.bot.send_message(
            chat_id=word_setter_chat_id,
            text=WORD_SETTER_WIN_MESSAGE.format(guesser_username=guesser_username),
            parse_mode='Markdown'
        )

        # Удаляем игру
        delete_game(word_setter_username, guesser_username)

        # Сбрасываем команды для обоих игроков
        await context.bot.set_my_commands([
            ("start", START_COMMAND_DESCRIPTION),
            ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
            ("cancel", CANCEL_COMMAND_DESCRIPTION)
        ], scope=BotCommandScopeChat(game['word_setter_chat_id']))

        await context.bot.set_my_commands([
            ("start", START_COMMAND_DESCRIPTION),
            ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
            ("cancel", CANCEL_COMMAND_DESCRIPTION)
        ], scope=BotCommandScopeChat(game['guesser_chat_id']))

        # Обновляем последнего партнёра
        user_data[word_setter_username]['last_partner'] = guesser_username
        user_data[guesser_username]['last_partner'] = word_setter_username
        save_user_data()
    else:
        if attempt_number >= game['max_attempts']:
            # Логируем проигрыш
            logging.info(
                f"Game lost - Guesser: {guesser_username} lost against {word_setter_username}, "
                f"Secret word: {secret_word}, "
                f"All {game['max_attempts']} attempts used"
            )

            await update.message.reply_text(
                OUT_OF_ATTEMPTS_MESSAGE.format(secret_word=secret_word.upper()),
                parse_mode='Markdown'
            )
            # Информируем загадавшего игрока
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=WORD_SETTER_LOSS_MESSAGE.format(guesser_username=guesser_username),
                parse_mode='Markdown'
            )
            # Удаляем игру
            del games[(word_setter_username, guesser_username)]

            # Сбрасываем команды для обоих игроков
            await context.bot.set_my_commands([
                ("start", START_COMMAND_DESCRIPTION),
                ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
                ("cancel", CANCEL_COMMAND_DESCRIPTION)
            ], scope=BotCommandScopeChat(game['word_setter_chat_id']))

            await context.bot.set_my_commands([
                ("start", START_COMMAND_DESCRIPTION),
                ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
                ("cancel", CANCEL_COMMAND_DESCRIPTION)
            ], scope=BotCommandScopeChat(game['guesser_chat_id']))
        else:
            remaining_attempts = game['max_attempts'] - attempt_number
            await update.message.reply_text(
                TRY_AGAIN_MESSAGE.format(remaining_attempts=remaining_attempts),
                parse_mode='Markdown'
            )


async def handle_last_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия на кнопку с последним партнёром"""
    query = update.callback_query
    await query.answer()
    last_partner_username = query.data.replace('last_partner_', '')
    word_setter_username = update.effective_user.username
    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = last_partner_username

    # Создаём новую игру
    word_setter_chat_id = user_data[word_setter_username]['chat_id']
    guesser_chat_id = user_data[last_partner_username]['chat_id']
    create_game(word_setter_username, last_partner_username, word_setter_chat_id, guesser_chat_id)

    # Сохраняем последнего партнёра
    user_data[word_setter_username]['last_partner'] = last_partner_username
    save_user_data()

    await query.edit_message_text(
        text=WORD_PROMPT_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )

    # Уведомляем второго игрока, что первый игрок загадывает слово
    await context.bot.send_message(
        chat_id=guesser_chat_id,
        text=SECOND_PLAYER_WAITING_MESSAGE.format(word_setter_username=word_setter_username),
        parse_mode='Markdown'
    )

    return WAITING_FOR_WORD

async def main():
    """Основная функция запуска бота"""
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_game', new_game)],
        states={
            WAITING_FOR_SECOND_PLAYER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_player),
                CallbackQueryHandler(handle_last_partner, pattern='^last_partner_')
            ],
            WAITING_FOR_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_word)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('addtry', addtry))
    say_handler = ConversationHandler(
        entry_points=[CommandHandler('say', say)],
        states={
            SAY_WAITING_FOR_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_say_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(say_handler)
    application.add_handler(CommandHandler('addtry', addtry))
    # Обработчик догадок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_word))


    # Set bot commands for the command hints
    await application.bot.set_my_commands([
        ("start", START_COMMAND_DESCRIPTION),
        ("new_game", NEW_GAME_COMMAND_DESCRIPTION),
        ("cancel", CANCEL_COMMAND_DESCRIPTION),
        ("say", SAY_COMMAND_DESCRIPTION),
        ("addtry", ADDTRY_COMMAND_DESCRIPTION)
    ])

    await application.run_polling()


if __name__ == '__main__':
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    finally:
        save_user_data()

