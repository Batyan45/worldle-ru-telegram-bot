"""Core game logic and state management."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from src.config.settings import MAX_ATTEMPTS


@dataclass
class Game:
    """
    Represents a game session between two players.
    
    Attributes:
        word_setter_username: Username of the player who sets the word.
        guesser_username: Username of the player who guesses the word.
        word_setter_chat_id: Chat ID of the word setter.
        guesser_chat_id: Chat ID of the guesser.
        secret_word: The word to be guessed.
        state: Current state of the game.
        attempts: List of attempts made by the guesser.
        max_attempts: Maximum number of attempts allowed.
        language: Language of the game (russian or english).
        correct_letters: Set of correctly guessed letters.
        used_letters: Set of used letters.
    """
    word_setter_username: str
    guesser_username: str
    word_setter_chat_id: int
    guesser_chat_id: int
    secret_word: str = ""
    state: str = "waiting_for_word"
    attempts: List[Tuple[str, str]] = field(default_factory=list)
    max_attempts: int = MAX_ATTEMPTS
    language: Optional[str] = None
    correct_letters: Set[str] = field(default_factory=set)
    used_letters: Set[str] = field(default_factory=set)


# Global game state
games: Dict[Tuple[str, str], Game] = {}


def create_game(
    word_setter_username: str,
    guesser_username: str,
    word_setter_chat_id: int,
    guesser_chat_id: int
) -> Game:
    """
    Create a new game instance.
    
    Args:
        word_setter_username: Username of the word setter.
        guesser_username: Username of the guesser.
        word_setter_chat_id: Chat ID of the word setter.
        guesser_chat_id: Chat ID of the guesser.
        
    Returns:
        Game: The newly created game instance.
    """
    game = Game(
        word_setter_username=word_setter_username,
        guesser_username=guesser_username,
        word_setter_chat_id=word_setter_chat_id,
        guesser_chat_id=guesser_chat_id
    )
    games[(word_setter_username, guesser_username)] = game
    return game


def get_game(word_setter_username: str, guesser_username: str) -> Optional[Game]:
    """
    Get an existing game by players' usernames.
    
    Args:
        word_setter_username: Username of the word setter.
        guesser_username: Username of the guesser.
        
    Returns:
        Optional[Game]: The game instance if found, None otherwise.
    """
    return games.get((word_setter_username, guesser_username))


def delete_game(word_setter_username: str, guesser_username: str) -> None:
    """
    Delete a game instance.
    
    Args:
        word_setter_username: Username of the word setter.
        guesser_username: Username of the guesser.
    """
    if (word_setter_username, guesser_username) in games:
        del games[(word_setter_username, guesser_username)]


def get_feedback(secret_word: str, guess: str) -> Tuple[str, str, Set[str], Set[str]]:
    """
    Generate feedback for a guess attempt.
    
    Args:
        secret_word: The word to be guessed.
        guess: The guessed word.
        
    Returns:
        Tuple containing:
        - result: The guess result with colored squares
        - feedback: Detailed feedback string
        - correct_letters: Set of correctly guessed letters
        - used_letters: Set of used letters
    """
    # Normalize 'Ё' to 'Е' in both secret word and guess
    secret_word = secret_word.replace('ё', 'е').replace('Ё', 'Е')
    guess = guess.replace('ё', 'е').replace('Ё', 'Е')
    
    feedback = ""
    result = ""
    correct_letters = set()
    used_letters = set()
    
    # Create a list to track used positions for yellow marks
    secret_chars = list(secret_word)
    marked_positions = set()

    # First pass - mark green squares
    for i, (s_char, g_char) in enumerate(zip(secret_word, guess)):
        if g_char == s_char:
            feedback += "🟩"
            result += g_char.upper()
            correct_letters.add(g_char.upper())
            marked_positions.add(i)
            secret_chars[i] = None  # Mark as used
        else:
            feedback += " "  # Placeholder
            result += " "   # Placeholder

    # Second pass - mark yellow and white squares
    for i, g_char in enumerate(guess):
        if i in marked_positions:
            continue
            
        g_char_upper = g_char.upper()
        result = result[:i] + g_char_upper + result[i+1:]
        
        if g_char in secret_chars:
            feedback = feedback[:i] + "🟨" + feedback[i+1:]
            correct_letters.add(g_char_upper)
            secret_chars.remove(g_char)  # Remove first occurrence
        else:
            feedback = feedback[:i] + "⬜" + feedback[i+1:]
            used_letters.add(g_char_upper)
            
    return result, feedback, correct_letters, used_letters 