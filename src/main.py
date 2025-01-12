"""Main application entry point."""

import asyncio
import logging
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.request import HTTPXRequest

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.utils.logger import setup_logger
from src.bot.commands import (
    DEFAULT_COMMANDS,
    WORD_SETTER_COMMANDS,
    GUESSER_COMMANDS
)
from src.bot.handlers.start import start_command
from src.bot.handlers.game import (
    new_game_command,
    set_player,
    receive_word,
    cancel_command,
    handle_last_partner,
    WAITING_FOR_SECOND_PLAYER,
    WAITING_FOR_WORD
)
from src.bot.handlers.say import (
    say_command,
    receive_say_message,
    SAY_WAITING_FOR_MESSAGE
)
from src.bot.handlers.addtry import addtry_command
from src.bot.handlers.guess import handle_guess
from src.core.user import save_user_data


async def main() -> None:
    """Main function to start the bot."""
    # Set up logging
    game_logger, system_logger = setup_logger()

    try:
        # Create the application with proper timeout settings
        request = HTTPXRequest(
            connection_pool_size=8,
            connect_timeout=10.0,
            read_timeout=10.0,
            write_timeout=10.0,
        )
        
        application = (
            ApplicationBuilder()
            .token(TELEGRAM_BOT_TOKEN)
            .request(request)
            .concurrent_updates(True)
            .build()
        )

        # Create conversation handlers
        game_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('new_game', new_game_command)],
            states={
                WAITING_FOR_SECOND_PLAYER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, set_player),
                    CallbackQueryHandler(handle_last_partner, pattern='^last_partner_')
                ],
                WAITING_FOR_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_word)],
            },
            fallbacks=[CommandHandler('cancel', cancel_command)],
            per_message=False
        )

        say_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('say', say_command)],
            states={
                SAY_WAITING_FOR_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_say_message)],
            },
            fallbacks=[CommandHandler('cancel', cancel_command)],
            per_message=False
        )

        # Add handlers
        handlers = [
            CommandHandler('start', start_command),
            game_conv_handler,
            say_conv_handler,
            CommandHandler('addtry', addtry_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess)
        ]

        for handler in handlers:
            application.add_handler(handler)

        # Set default bot commands
        await application.bot.set_my_commands([
            (cmd.command, cmd.description) for cmd in DEFAULT_COMMANDS
        ])

        # Start the bot
        system_logger.info("Starting bot...")
        await application.run_polling(drop_pending_updates=True)

    except Exception as e:
        system_logger.error(f"Error running bot: {str(e)}", exc_info=True)
        raise
    finally:
        # Ensure we save user data on shutdown
        save_user_data()
        system_logger.info("Bot stopped")


if __name__ == '__main__':
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot stopped due to error: {str(e)}")
    finally:
        save_user_data() 