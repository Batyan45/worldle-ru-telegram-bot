import pytest
import sys
import asyncio
from telegram import User, Message, Chat, Update
from telegram.ext import ContextTypes
from telegram.ext import ApplicationBuilder
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import start, new_game, set_player, receive_word, guess_word, cancel

@pytest.mark.asyncio
async def test_start():
    user = User(id=1, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="/start", from_user=user)
    update = Update(update_id=1, message=message)
    application = ApplicationBuilder().token("TEST_TOKEN").build()
    context = ContextTypes.DEFAULT_TYPE(application=application)

    await start(update, context)
    assert update.message.text == "Привет! Это игра для двух игроков в стиле Wordle.\nИспользуй команду /new_game, чтобы начать новую игру."

@pytest.mark.asyncio
async def test_new_game():
    user = User(id=1, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="/new_game", from_user=user)
    update = Update(update_id=1, message=message)
    context = ContextTypes.DEFAULT_TYPE()

    result = await new_game(update, context)
    assert result == 0  # ConversationHandler.END

@pytest.mark.asyncio
async def test_set_player():
    user = User(id=1, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="@secondplayer", from_user=user)
    update = Update(update_id=1, message=message)
    context = ContextTypes.DEFAULT_TYPE()
    context.user_data = {}

    result = await set_player(update, context)
    assert result == 1  # WAITING_FOR_WORD

@pytest.mark.asyncio
async def test_receive_word():
    user = User(id=1, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="apple", from_user=user)
    update = Update(update_id=1, message=message)
    context = ContextTypes.DEFAULT_TYPE()
    context.user_data = {'word_setter_username': 'testuser', 'guesser_username': 'secondplayer'}

    result = await receive_word(update, context)
    assert result == 0  # ConversationHandler.END

@pytest.mark.asyncio
async def test_guess_word():
    user = User(id=1, first_name="Test", is_bot=False, username="secondplayer")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="apple", from_user=user)
    update = Update(update_id=1, message=message)
    context = ContextTypes.DEFAULT_TYPE()

    await guess_word(update, context)
    assert update.message.text.startswith("Попытка 1:")

@pytest.mark.asyncio
async def test_cancel():
    user = User(id=1, first_name="Test", is_bot=False, username="testuser")
    chat = Chat(id=1, type="private")
    message = Message(message_id=1, date=None, chat=chat, text="/cancel", from_user=user)
    update = Update(update_id=1, message=message)
    context = ContextTypes.DEFAULT_TYPE()

    result = await cancel(update, context)
    assert result == 0  # ConversationHandler.END
