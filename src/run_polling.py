import asyncio
import logging
import sys
from bot.bot import bot, dp


async def run_polling() -> None:
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(run_polling())
