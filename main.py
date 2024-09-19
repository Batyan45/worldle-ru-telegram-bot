# main.py

import logging
from telegram import Update
from config import TELEGRAM_BOT_TOKEN
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Этапы разговора
WAITING_FOR_SECOND_PLAYER, WAITING_FOR_WORD = range(2)

# Словарь для хранения состояния игр
games = {}

# Словарь для хранения chat_id пользователей по username
user_chat_ids = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.message.from_user
    username = user.username
    chat_id = update.message.chat_id
    # Сохраняем chat_id пользователя
    if username:
        user_chat_ids[username] = chat_id
        await update.message.reply_text(
            "Привет! Это игра для двух игроков в стиле Wordle.\n"
            "Используй команду /new_game, чтобы начать новую игру."
        )
    else:
        await update.message.reply_text(
            "Привет! Пожалуйста, установи username в Telegram, чтобы использовать этого бота."
        )


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new_game для начала новой игры"""
    user = update.message.from_user
    username = user.username
    if not username:
        await update.message.reply_text(
            "Пожалуйста, установи username в Telegram, чтобы использовать этого бота."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Отправь @username второго игрока, с которым хочешь сыграть."
    )
    return WAITING_FOR_SECOND_PLAYER


async def set_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установка второго игрока"""
    second_player = update.message.text.strip()
    if not second_player.startswith('@'):
        second_player = '@' + second_player  # Добавляем '@' в начало
    second_player_username = second_player[1:]  # Убираем '@'

    if second_player_username not in user_chat_ids:
        await update.message.reply_text(
            f"Игрок {second_player} ещё не начал диалог с ботом. Попроси его отправить команду /start боту."
        )
        return WAITING_FOR_SECOND_PLAYER

    word_setter_username = update.message.from_user.username
    word_setter_chat_id = update.message.chat_id
    context.user_data['word_setter_username'] = word_setter_username
    context.user_data['guesser_username'] = second_player_username

    guesser_chat_id = user_chat_ids[second_player_username]

    # Создаём новую игру
    games[(word_setter_username, second_player_username)] = {
        'state': 'waiting_for_word',
        'secret_word': '',
        'attempts': [],
        'word_setter_chat_id': word_setter_chat_id,
        'guesser_chat_id': guesser_chat_id
    }

    await update.message.reply_text(
        f"Отлично! Теперь, {word_setter_username}, загадай слово из 5 букв."
    )
    return WAITING_FOR_WORD


async def receive_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение загаданного слова и начало игры"""
    word = update.message.text.strip().lower()
    if len(word) != 5 or not word.isalpha():
        await update.message.reply_text("Слово должно состоять из 5 букв. Попробуй снова.")
        return WAITING_FOR_WORD

    word_setter_username = context.user_data['word_setter_username']
    guesser_username = context.user_data['guesser_username']
    game = games.get((word_setter_username, guesser_username))

    if game and game['state'] == 'waiting_for_word':
        game['secret_word'] = word
        game['state'] = 'waiting_for_guess'
        await update.message.reply_text("Слово загадано!")

        # Отправляем сообщение угадывающему
        guesser_chat_id = game['guesser_chat_id']
        await context.bot.send_message(
            chat_id=guesser_chat_id,
            text=f"{word_setter_username} загадал(а) слово из 5 букв. Попробуй угадать его!"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Произошла ошибка. Попробуйте начать новую игру.")
        return ConversationHandler.END


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


async def guess_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка догадок игрока"""
    guesser_username = update.message.from_user.username
    message = update.message.text.strip().lower()
    if len(message) != 5 or not message.isalpha():
        await update.message.reply_text("Догадка должна состоять из 5 букв.")
        return

    # Поиск соответствующей игры
    game = None
    word_setter_username = None
    for (w_s_username, g_username), g in games.items():
        if g_username == guesser_username and g['state'] == 'waiting_for_guess':
            game = g
            word_setter_username = w_s_username
            break

    if not game:
        await update.message.reply_text("У вас нет активных игр. Начните новую с помощью команды /new_game.")
        return

    secret_word = game['secret_word']
    result, feedback = get_feedback(secret_word, message)
    game['attempts'].append((result, feedback))

    attempt_number = len(game['attempts'])

    # Формируем сообщение с последней попыткой и номером
    attempt_text = f"Попытка {attempt_number}:\n{result}\n{feedback}"

    await update.message.reply_text(attempt_text)

    # Отправляем попытку загадавшему игроку с припиской
    word_setter_chat_id = game['word_setter_chat_id']
    await context.bot.send_message(
        chat_id=word_setter_chat_id,
        text=f"Игрок {guesser_username} сделал попытку {attempt_number}:\n{result}\n{feedback}"
    )

    if message == secret_word:
        await update.message.reply_text("🎉 Поздравляем! Вы угадали слово! 🎉")

        # Отправляем сообщение загадывающему
        await context.bot.send_message(
            chat_id=word_setter_chat_id,
            text=f"Игрок {guesser_username} угадал ваше слово!"
        )

        # Удаляем игру
        del games[(word_setter_username, guesser_username)]
    else:
        if attempt_number >= 6:
            await update.message.reply_text(f"К сожалению, попытки закончились. Вы не смогли угадать слово '{secret_word.upper()}'.")
            # Информируем загадавшего игрока
            await context.bot.send_message(
                chat_id=word_setter_chat_id,
                text=f"Игрок {guesser_username} не смог угадать ваше слово за 6 попыток."
            )
            # Удаляем игру
            del games[(word_setter_username, guesser_username)]
        else:
            remaining_attempts = 6 - attempt_number
            await update.message.reply_text(f"Попробуйте еще раз. Осталось попыток: {remaining_attempts}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена игры"""
    await update.message.reply_text("Игра прервана.")
    return ConversationHandler.END


def main():
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

    application.run_polling()


if __name__ == '__main__':
    main()
