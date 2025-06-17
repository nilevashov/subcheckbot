from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.exceptions import TelegramBadRequest
from bot import bot


async def send_message(
    message: Message, message_text: str, keyboard: InlineKeyboardMarkup, **kwargs: dict
):
    try:
        return await bot.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            chat_id=message.chat.id,
            message_id=message.message_id,
            **kwargs
        )
    except TelegramBadRequest:
        return await message.answer(text=message_text, reply_markup=keyboard, **kwargs)
