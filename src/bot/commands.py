"""Bot command definitions and descriptions."""

from dataclasses import dataclass
from typing import List


@dataclass
class BotCommand:
    """
    Represents a bot command.
    
    Attributes:
        command: The command name without the slash.
        description: The command description shown in the menu.
    """
    command: str
    description: str


# Command descriptions
START_COMMAND = BotCommand("start", "Start the bot and get information")
NEW_GAME_COMMAND = BotCommand("new_game", "Start a new game with another player")
CANCEL_COMMAND = BotCommand("cancel", "Cancel the current game")
SAY_COMMAND = BotCommand("say", "Send a message to your game partner")
ADDTRY_COMMAND = BotCommand("addtry", "Add one attempt for the guessing player")


# Command groups
DEFAULT_COMMANDS: List[BotCommand] = [
    START_COMMAND,
    NEW_GAME_COMMAND,
    CANCEL_COMMAND,
    SAY_COMMAND,
    ADDTRY_COMMAND
]

WORD_SETTER_COMMANDS: List[BotCommand] = [
    START_COMMAND,
    SAY_COMMAND,
    CANCEL_COMMAND,
    ADDTRY_COMMAND
]

GUESSER_COMMANDS: List[BotCommand] = [
    START_COMMAND,
    SAY_COMMAND,
    CANCEL_COMMAND
] 