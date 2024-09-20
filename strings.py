
START_MESSAGE = (
    "Привет! Это игра для двух игроков в стиле Wordle.\n"
    "Используй команду /new_game, чтобы начать новую игру."
)
NO_USERNAME_MESSAGE = (
    "Привет! Пожалуйста, установи username в Telegram, чтобы использовать этого бота."
)
NEW_GAME_MESSAGE = "Отправь @username второго игрока, с которым хочешь сыграть."
NO_USERNAME_NEW_GAME_MESSAGE = (
    "Пожалуйста, установи username в Telegram, чтобы использовать этого бота."
)
SECOND_PLAYER_WAITING_MESSAGE = (
    "Игрок {word_setter_username} сейчас загадывает слово. Пожалуйста, подождите."
)
SECOND_PLAYER_NOT_STARTED_MESSAGE = (
    "Игрок {second_player} ещё не начал диалог с ботом. Попроси его отправить команду /start боту."
)
SECOND_PLAYER_HAS_ACTIVE_GAME_MESSAGE = (
    "Игрок {second_player} уже начал игру. Попросите его отменить текущую игру, чтобы его можно было пригласить."
)
WORD_PROMPT_MESSAGE = "Отлично! Теперь, {word_setter_username}, загадай слово из 5 букв."
INVALID_WORD_MESSAGE = "Слово должно состоять из 5 букв. Попробуй снова."
WORD_SET_MESSAGE = "Слово загадано!"
GUESS_PROMPT_MESSAGE = "{word_setter_username} загадал(а) слово из 5 букв. Попробуй угадать его!"
NO_ACTIVE_GAME_MESSAGE = "У вас нет активных игр. Начните новую с помощью команды /new_game."
INVALID_GUESS_MESSAGE = "Догадка должна состоять из 5 букв."
ATTEMPT_MESSAGE = "Попытка {attempt_number}:\n{result}\n{feedback}"
GUESSER_WIN_MESSAGE = "🎉 Поздравляем! Вы угадали слово! 🎉"
WORD_SETTER_WIN_MESSAGE = "Игрок {guesser_username} угадал ваше слово!"
OUT_OF_ATTEMPTS_MESSAGE = (
    "К сожалению, попытки закончились. Вы не смогли угадать слово '{secret_word}'."
)
WORD_SETTER_LOSS_MESSAGE = (
    "Игрок {guesser_username} не смог угадать ваше слово за 6 попыток."
)
TRY_AGAIN_MESSAGE = "Попробуйте еще раз. Осталось попыток: {remaining_attempts}"
CANCEL_MESSAGE = "Игра прервана."
ERROR_MESSAGE = "Произошла ошибка. Попробуйте начать новую игру."
START_COMMAND_DESCRIPTION = "Начать взаимодействие с ботом"
NEW_GAME_COMMAND_DESCRIPTION = "Создать новую игру"
CANCEL_COMMAND_DESCRIPTION = "Отменить текущую игру"
