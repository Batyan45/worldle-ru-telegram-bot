"""Inline keyboard definitions for the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_last_partner_keyboard(last_partner: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with a button to play with the last partner.
    
    Args:
        last_partner: Username of the last game partner.
        
    Returns:
        InlineKeyboardMarkup: The keyboard markup object.
    """
    keyboard = [[InlineKeyboardButton(f"Play with @{last_partner}", callback_data=f"last_partner_{last_partner}")]]
    return InlineKeyboardMarkup(keyboard) 