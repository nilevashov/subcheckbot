from typing import Callable, Dict, Any, Awaitable

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject


class AdminAuthMiddleware(BaseMiddleware):
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

        if message.chat.id == 468761425:
            return await handler(event, data)

        return False
