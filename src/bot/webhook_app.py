import traceback
from typing import AsyncGenerator

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from db import create_tables
from settings import config
from aiogram.types import Update, FSInputFile
from contextlib import asynccontextmanager
import sentry_sdk
from loguru import logger

from .bot import dp, bot


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Контекстный менеджер для управления жизненным циклом приложения"""

    await create_tables()
    await bot.set_webhook(
        url=config.telegram.webhook.url,
        certificate=(
            FSInputFile(config.telegram.webhook.ssl_cert)
            if config.telegram.webhook.ssl_cert
            else None
        ),
    )
    logger.success(f"Webhook установлен: {config.telegram.webhook.url}")
    yield
    await bot.delete_webhook()
    await bot.session.close()
    logger.success("Webhook удален, бот отключен.")


webhook_app = FastAPI(lifespan=lifespan)
Instrumentator().instrument(webhook_app).expose(webhook_app)


@webhook_app.post(config.telegram.webhook.path)
async def webhook_handler(update: Update) -> dict[str, str]:
    try:
        from_username = None

        if update.message:
            from_username = update.message.from_user.username if update.message.from_user else None
        elif update.callback_query:
            from_username = (
                update.callback_query.from_user.username
                if update.callback_query.from_user
                else None
            )

        if config.debug:
            logger.info(f"Got update | update_id={update.update_id} | from={from_username}")

        await dp.feed_webhook_update(bot, update)
    except Exception as ex:
        sentry_sdk.capture_exception(ex)
        logger.error(traceback.format_exc())
    return {"status": "ok"}
