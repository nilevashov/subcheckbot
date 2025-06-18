from typing import Callable, Dict, Any, Awaitable

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject

from settings import config
from db import rd


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, types.Message):
            message = event
        elif isinstance(event, types.CallbackQuery) and isinstance(event.message, types.Message):
            message = event.message
        else:
            return await handler(event, data)

        if message.text == "/start" or message.chat.type != "private":
            return await handler(event, data)

        rd_key = f"{config.redis.prefix}:{message.chat.id}"
        user_status = await rd.hget(rd_key, "status")

        if user_status == b"False":
            await message.answer(
                "Доступ к боту ограничен. За активацией обратитесь к @yocan_uc",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return False

        return await handler(event, data)
