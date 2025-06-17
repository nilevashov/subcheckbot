from aiogram import Router

from middlewares.auth import AuthMiddleware
from .admin_menu import admin_router
from .channel_menu import channel_router
from .chat_menu import chat_router
from .start import start_router
from .settings import settings_router
from .group_messages_handler import group_router

from bot import dp

main_router = Router()

main_router.include_router(start_router)
main_router.include_router(settings_router)
main_router.include_router(group_router)
main_router.include_router(channel_router)
main_router.include_router(chat_router)
main_router.include_router(admin_router)

dp.include_router(main_router)

main_router.message.middleware(AuthMiddleware())
main_router.callback_query.middleware(AuthMiddleware())
