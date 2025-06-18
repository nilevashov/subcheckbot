from typing import Any

from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot import bot


async def send_message(
    message: Message, message_text: str, keyboard: InlineKeyboardMarkup
) -> None:
    try:
        await bot.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            chat_id=message.chat.id,
            message_id=message.message_id
        )
    except TelegramBadRequest:
        await message.answer(text=message_text, reply_markup=keyboard)

def get_callback_message(callback: CallbackQuery) -> Message:
    if not isinstance(callback.message, Message):
        raise ValueError("callback.message must be Message")
    return callback.message