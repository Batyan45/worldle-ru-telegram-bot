"""Bot command definitions and descriptions."""

import logging
from dataclasses import dataclass
from typing import List

from telegram import Update, BotCommand as TgBotCommand
from telegram.ext import ContextTypes
from telegram._botcommandscope import BotCommandScopeChat

from src.core.game import get_user_role


@dataclass
class CommandDef:
    """
    Represents a bot command.
    
    Attributes:
        command: The command name without the slash.
        description: The command description shown in the menu.
    """
    command: str
    description: str


# Command descriptions
START_COMMAND = CommandDef("start", "Start the bot and get information")
NEW_GAME_COMMAND = CommandDef("new_game", "Start a new game with another player")
CANCEL_COMMAND = CommandDef("cancel", "Cancel the current game")
SAY_COMMAND = CommandDef("say", "Send a message to your game partner")
ADDTRY_COMMAND = CommandDef("addtry", "Add one attempt for the guessing player")


# Command groups
DEFAULT_COMMANDS: List[CommandDef] = [
    START_COMMAND,
    NEW_GAME_COMMAND,
    CANCEL_COMMAND
]

WORD_SETTER_COMMANDS: List[CommandDef] = [
    START_COMMAND,
    SAY_COMMAND,
    CANCEL_COMMAND,
    ADDTRY_COMMAND
]

GUESSER_COMMANDS: List[CommandDef] = [
    START_COMMAND,
    SAY_COMMAND,
    CANCEL_COMMAND
]


async def update_user_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Update the bot commands shown to a user based on their role.
    
    Args:
        update: The update object from Telegram.
        context: The context object for the callback.
    """
    user = update.effective_user
    if not user or not user.username:
        return

    role = get_user_role(user.username)
    commands = []

    if role == "word_setter":
        commands = [TgBotCommand(command=cmd.command, description=cmd.description) for cmd in WORD_SETTER_COMMANDS]
    elif role == "guesser":
        commands = [TgBotCommand(command=cmd.command, description=cmd.description) for cmd in GUESSER_COMMANDS]
    else:
        commands = [TgBotCommand(command=cmd.command, description=cmd.description) for cmd in DEFAULT_COMMANDS]

    try:
        await context.bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeChat(chat_id=update.effective_chat.id),
        )
    except Exception as e:
        logging.error(f"Failed to update commands for user {user.username}: {e}") 