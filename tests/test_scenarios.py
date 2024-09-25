import unittest
from unittest.mock import AsyncMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes
from main import start, new_game, set_player, receive_word, cancel, guess_word, handle_last_partner
from game import games, delete_game
from user import user_data, save_user_data

class TestGameScenarios(unittest.IsolatedAsyncioTestCase):
    """Тестовые сценарии для Telegram-бота Wordle"""

    async def test_game_cancellation_at_any_stage(self):
        """Проверка отмены игры на различных этапах"""
        # Мокаем данные обновления и контекста
        update = AsyncMock()
        update.message = AsyncMock()
        context = AsyncMock()
        context.bot = AsyncMock()

        update.message.text = '/cancel'
        update.message.from_user.username = 'tester'
        await cancel(update, context)
        update.message.reply_text.assert_called_with('Игра прервана.', parse_mode='Markdown')

    async def test_correct_game_flow(self):
        """Проверка корректного прохождения игры"""
        # Симулируем двух пользователей
        user1 = User(id=1, first_name='Player1', username='player1', is_bot=False)
        user2 = User(id=2, first_name='Player2', username='player2', is_bot=False)

        # Мокаем обновления и контексты
        update1 = AsyncMock()
        context1 = AsyncMock()
        update2 = AsyncMock()
        context2 = AsyncMock()

        # Пользователь 1 отправляет команду /start
        update1.message.from_user = user1
        update1.message.chat_id = 1001
        update1.message.text = '/start'
        await start(update1, context1)

        # Пользователь 2 отправляет команду /start
        update2.message.from_user = user2
        update2.message.chat_id = 1002
        update2.message.text = '/start'
        await start(update2, context2)

        # Пользователь 1 начинает новую игру с пользователем 2
        update1.message.text = '/new_game'
        await new_game(update1, context1)

        # Пользователь 1 устанавливает второго игрока
        update1.message.text = '@player2'
        context1.user_data = {}
        await set_player(update1, context1)

        # Пользователь 1 загадывает слово
        update1.message.text = 'слово'
        await receive_word(update1, context1)

        # Пользователь 2 делает догадку
        update2.message.from_user = user2
        update2.message.text = 'слово'
        await guess_word(update2, context2)

        # Проверяем, что игра завершена и удалена
        self.assertNotIn(('player1', 'player2'), games)

    async def test_game_cancellation_during_word_setting(self):
        """Проверка отмены игры во время задания слова"""
        # Симулируем пользователя
        user = User(id=1, first_name='Player', username='player', is_bot=False)

        # Мокаем обновления и контекст
        update = AsyncMock()
        context = AsyncMock()

        # Пользователь начинает новую игру
        update.message.from_user = user
        update.message.chat_id = 1001
        update.message.text = '/new_game'
        await new_game(update, context)

        # Отмена игры
        update.message.text = '/cancel'
        await cancel(update, context)

        # Проверяем, что игра не существует
        self.assertNotIn(('player', context.user_data.get('guesser_username')), games)

    async def test_two_players_starting_simultaneous_games(self):
        """Проверка ситуации, когда два игрока начинают игру одновременно"""
        # Симулируем двух пользователей
        user1 = User(id=1, first_name='Player1', username='player1', is_bot=False)
        user2 = User(id=2, first_name='Player2', username='player2', is_bot=False)

        # Мокаем обновления и контексты
        update1 = AsyncMock()
        context1 = AsyncMock()
        update2 = AsyncMock()
        context2 = AsyncMock()

        # Оба пользователя отправляют команду /start
        update1.message.from_user = user1
        update1.message.chat_id = 1001
        await start(update1, context1)

        update2.message.from_user = user2
        update2.message.chat_id = 1002
        await start(update2, context2)

        # Оба пользователя начинают новую игру
        update1.message.text = '/new_game'
        await new_game(update1, context1)

        update2.message.text = '/new_game'
        await new_game(update2, context2)

        # Оба устанавливают друг друга как соперников
        update1.message.text = '@player2'
        context1.user_data = {}
        await set_player(update1, context1)

        update2.message.text = '@player1'
        context2.user_data = {}
        await set_player(update2, context2)

        # Проверяем, что созданы две отдельные игры
        self.assertIn(('player1', 'player2'), games)
        self.assertIn(('player2', 'player1'), games)

    async def test_invalid_word_input(self):
        """Проверка ввода некорректного слова"""
        # Симулируем пользователя
        user = User(id=1, first_name='Player', username='player', is_bot=False)

        # Мокаем обновление и контекст
        update = AsyncMock()
        context = AsyncMock()

        # Пользователь отправляет некорректное слово
        update.message.from_user = user
        update.message.text = 'сл'
        await receive_word(update, context)

        # Проверяем, что вывелось сообщение об ошибке
        update.message.reply_text.assert_called_with('Слово должно состоять из 5 букв. Попробуй снова.', parse_mode='Markdown')

    async def test_guess_without_active_game(self):
        """Проверка попытки догадки без активной игры"""
        # Симулируем пользователя
        user = User(id=1, first_name='Player', username='player', is_bot=False)

        # Мокаем обновление и контекст
        update = AsyncMock()
        context = AsyncMock()

        # Пользователь пытается угадать слово без активной игры
        update.message.from_user = user
        update.message.text = 'слово'
        await guess_word(update, context)

        # Проверяем, что вывелось сообщение об отсутствии активной игры
        update.message.reply_text.assert_called_with('У вас нет активных игр. Начните новую с помощью команды /new_game.', parse_mode='Markdown')

    async def test_game_flow_with_incorrect_guesses(self):
        """Проверка игры с неправильными догадками и исчерпанием попыток"""
        # Симулируем двух пользователей
        user1 = User(id=1, first_name='Player1', username='player1', is_bot=False)
        user2 = User(id=2, first_name='Player2', username='player2', is_bot=False)

        # Мокаем обновления и контексты
        update1 = AsyncMock()
        context1 = AsyncMock()
        update2 = AsyncMock()
        context2 = AsyncMock()

        # Пользователи начинают игру и устанавливают друг друга
        update1.message.from_user = user1
        update1.message.chat_id = 1001
        update2.message.from_user = user2
        update2.message.chat_id = 1002

        # /start команды
        update1.message.text = '/start'
        await start(update1, context1)
        update2.message.text = '/start'
        await start(update2, context2)

        # /new_game команды
        update1.message.text = '/new_game'
        await new_game(update1, context1)
        update1.message.text = '@player2'
        context1.user_data = {}
        await set_player(update1, context1)
        update1.message.text = 'слово'
        await receive_word(update1, context1)

        # Пользователь 2 делает 6 неправильных догадок
        update2.message.from_user = user2
        for i in range(6):
            update2.message.text = 'невер'
            await guess_word(update2, context2)

        # Проверяем, что игра удалена после 6 попыток
        self.assertNotIn(('player1', 'player2'), games)

if __name__ == '__main__':
    unittest.main()
