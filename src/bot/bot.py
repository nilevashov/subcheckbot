
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from db import create_tables
from settings import config

import sentry_sdk
import logging
import sys


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def on_startup(bot: Bot) -> None:
    await create_tables()


if config.sentry.turned_on:
    sentry_sdk.init(
        dsn=config.sentry.dsn,
        traces_sample_rate=config.sentry.traces_sample_rate,
        profiles_sample_rate=config.sentry.profiles_sample_rate,
        sample_rate=config.sentry.sample_rate,
        environment=config.sentry.environment,
    )


bot = Bot(config.telegram.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
dp.startup.register(on_startup)

from . import handlers  # noqa: E402, F401, F811
