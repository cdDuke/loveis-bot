import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.database import create_connection, init_db
from bot.handlers import setup_routers
from bot.services.ai_service import AIService
from bot.services.travel_service import MockTravelProvider


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Add it to .env")

    await init_db(settings.database_path)
    db = await create_connection(settings.database_path)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    setup_routers(dp)

    dp["settings"] = settings
    dp["db"] = db
    dp["ai_service"] = AIService(settings.openai_api_key, settings.openai_model)
    dp["travel_provider"] = MockTravelProvider(settings.travel_sites)

    logging.info("LoveIS bot is starting")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

