"""Test scenarios for the Telegram Wordle bot game."""
from typing import TYPE_CHECKING, AsyncGenerator, Dict, Tuple

import pytest
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes, CallbackContext, Application, ExtBot

from src.bot.handlers.game import set_player, receive_word, cancel_command
from src.bot.handlers.guess import handle_guess
from src.bot.handlers.start import start_command
from src.core.game import Game, games, create_game, delete_game, get_feedback
from src.core.user import user_data
from src.config.strings import (
    INVALID_WORD_MESSAGE,
    NO_ACTIVE_GAME_MESSAGE,
    OUT_OF_ATTEMPTS_MESSAGE,
    GUESSER_WIN_MESSAGE,
    WORD_SETTER_WIN_MESSAGE,
    WORD_SETTER_LOSS_MESSAGE,
    TRY_AGAIN_MESSAGE
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_bot(mocker: "MockerFixture") -> ExtBot:
    """Create a mock bot for testing."""
    mock_bot = mocker.Mock(spec=ExtBot)
    mock_bot.send_message = mocker.AsyncMock()
    mock_bot.delete_message = mocker.AsyncMock()
    mock_bot.set_my_commands = mocker.AsyncMock()
    return mock_bot


@pytest.fixture
def mock_context(mock_bot: ExtBot) -> CallbackContext:
    """Create a mock Context object for testing."""
    mock_application = Application.builder().bot(mock_bot).build()
    
    # Create a context with empty dictionaries for data storage
    context = CallbackContext(mock_application)
    context._user_data = {}  # Use protected attribute to bypass immutability
    context._chat_data = {}
    context._bot_data = {}
    return context


@pytest.fixture(autouse=True)
async def cleanup_games() -> AsyncGenerator[None, None]:
    """Clean up games dictionary before and after each test."""
    games.clear()
    user_data.clear()
    yield
    games.clear()
    user_data.clear()


def create_message(chat: Chat, user: User, text: str, bot: ExtBot) -> Message:
    """Create a Message object with the given parameters."""
    return Message(
        message_id=1,
        date=None,
        chat=chat,
        from_user=user,
        text=text,
        bot=bot
    )


@pytest.mark.asyncio
async def test_game_creation_and_word_setting(
    mock_bot: ExtBot,
    mock_context: CallbackContext
) -> None:
    """
    Test game creation and word setting process.
    
    Args:
        mock_bot: Mock bot instance
        mock_context: Mock Context object
    """
    # Setup players
    word_setter = User(1, "word_setter", False, username="word_setter")
    guesser = User(2, "guesser", False, username="guesser")
    chat = Chat(1001, "private")
    
    # Mock user data
    user_data["word_setter"] = {"chat_id": 1001}
    user_data["guesser"] = {"chat_id": 1002}
    
    mock_context._user_data = {
        "word_setter_username": "word_setter",
        "guesser_username": "guesser"
    }
    
    # Set second player
    message = create_message(chat, word_setter, "@guesser", mock_bot)
    mock_update = Update(1, message=message)
    await set_player(mock_update, mock_context)
    
    assert ("word_setter", "guesser") in games
    game = games[("word_setter", "guesser")]
    assert game.state == "waiting_for_word"
    
    # Set word
    message = create_message(chat, word_setter, "слово", mock_bot)
    mock_update = Update(1, message=message)
    await receive_word(mock_update, mock_context)
    
    game = games[("word_setter", "guesser")]
    assert game.state == "waiting_for_guess"
    assert game.secret_word == "слово"
    assert game.language == "russian"


@pytest.mark.asyncio
async def test_word_guessing_process(
    mock_bot: ExtBot,
    mock_context: CallbackContext
) -> None:
    """
    Test the word guessing process including feedback.
    
    Args:
        mock_bot: Mock bot instance
        mock_context: Mock Context object
    """
    # Setup game
    game = Game(
        word_setter_username="word_setter",
        guesser_username="guesser",
        word_setter_chat_id=1001,
        guesser_chat_id=1002
    )
    game.secret_word = "слово"
    game.state = "waiting_for_guess"
    game.language = "russian"
    games[("word_setter", "guesser")] = game
    
    # Setup guesser
    guesser = User(2, "guesser", False, username="guesser")
    chat = Chat(1002, "private")
    
    # Test incorrect guess
    message = create_message(chat, guesser, "книга", mock_bot)
    mock_update = Update(1, message=message)
    await handle_guess(mock_update, mock_context)
    
    game = games[("word_setter", "guesser")]
    assert len(game.attempts) == 1
    assert game.state == "waiting_for_guess"
    
    # Test correct guess
    message = create_message(chat, guesser, "слово", mock_bot)
    mock_update = Update(1, message=message)
    await handle_guess(mock_update, mock_context)
    
    assert ("word_setter", "guesser") not in games  # Game should be deleted after win


@pytest.mark.asyncio
async def test_game_cancellation(
    mock_bot: ExtBot,
    mock_context: CallbackContext
) -> None:
    """
    Test game cancellation at different stages.
    
    Args:
        mock_bot: Mock bot instance
        mock_context: Mock Context object
    """
    # Setup game
    game = Game(
        word_setter_username="word_setter",
        guesser_username="guesser",
        word_setter_chat_id=1001,
        guesser_chat_id=1002
    )
    game.secret_word = "слово"
    game.state = "waiting_for_guess"
    games[("word_setter", "guesser")] = game
    
    # Cancel game as word setter
    word_setter = User(1, "word_setter", False, username="word_setter")
    chat = Chat(1001, "private")
    message = create_message(chat, word_setter, "/cancel", mock_bot)
    mock_update = Update(1, message=message)
    
    await cancel_command(mock_update, mock_context)
    
    assert ("word_setter", "guesser") not in games


@pytest.mark.asyncio
async def test_feedback_mechanism() -> None:
    """Test the feedback mechanism for guesses."""
    secret_word = "слово"
    test_cases = [
        ("книга", "КНИГА", "🟩🟨🟨⬜⬜"),  # First letter matches, 'и' and 'а' are in wrong positions
        ("солнц", "СОЛНЦ", "🟩⬜⬜⬜⬜"),  # Only first letter matches
        ("слово", "СЛОВО", "🟩🟩🟩🟩🟩"),  # Exact match
    ]
    
    for guess, expected_result, expected_feedback in test_cases:
        result, feedback, _, _ = get_feedback(secret_word, guess)
        assert result == expected_result
        assert feedback == expected_feedback


@pytest.mark.asyncio
async def test_max_attempts_limit(
    mock_bot: ExtBot,
    mock_context: CallbackContext
) -> None:
    """
    Test that the game ends after maximum attempts are reached.
    
    Args:
        mock_bot: Mock bot instance
        mock_context: Mock Context object
    """
    # Setup game
    game = Game(
        word_setter_username="word_setter",
        guesser_username="guesser",
        word_setter_chat_id=1001,
        guesser_chat_id=1002
    )
    game.secret_word = "слово"
    game.state = "waiting_for_guess"
    game.language = "russian"
    games[("word_setter", "guesser")] = game
    
    # Setup guesser
    guesser = User(2, "guesser", False, username="guesser")
    chat = Chat(1002, "private")
    
    # Make max_attempts incorrect guesses
    for _ in range(game.max_attempts):
        message = create_message(chat, guesser, "книга", mock_bot)
        mock_update = Update(1, message=message)
        await handle_guess(mock_update, mock_context)
    
    assert ("word_setter", "guesser") not in games  # Game should be deleted after max attempts


@pytest.mark.asyncio
async def test_invalid_inputs(
    mock_bot: ExtBot,
    mock_context: CallbackContext
) -> None:
    """
    Test handling of invalid inputs.
    
    Args:
        mock_bot: Mock bot instance
        mock_context: Mock Context object
    """
    # Setup game for word setting
    game = Game(
        word_setter_username="word_setter",
        guesser_username="guesser",
        word_setter_chat_id=1001,
        guesser_chat_id=1002
    )
    games[("word_setter", "guesser")] = game
    
    # Setup word setter
    word_setter = User(1, "word_setter", False, username="word_setter")
    chat = Chat(1001, "private")
    
    mock_context._user_data = {
        "word_setter_username": "word_setter",
        "guesser_username": "guesser"
    }
    
    # Test invalid word length
    message = create_message(chat, word_setter, "сл", mock_bot)
    mock_update = Update(1, message=message)
    await receive_word(mock_update, mock_context)
    assert game.secret_word == ""  # Word should not be set
    
    # Test mixed language
    message = create_message(chat, word_setter, "слоvo", mock_bot)
    mock_update = Update(1, message=message)
    await receive_word(mock_update, mock_context)
    assert game.secret_word == ""  # Word should not be set
    
    # Set valid word and test invalid guess
    game.secret_word = "слово"
    game.state = "waiting_for_guess"
    
    # Setup guesser
    guesser = User(2, "guesser", False, username="guesser")
    chat = Chat(1002, "private")
    
    # Test invalid guess length
    message = create_message(chat, guesser, "сло", mock_bot)
    mock_update = Update(1, message=message)
    await handle_guess(mock_update, mock_context)
    assert len(game.attempts) == 0  # Guess should not be recorded
