import asyncio
import importlib.metadata

from loguru import logger

from school_routine_bot.settings import get_settings

if __name__ == "__main__":
    logger.info(f"Version: {importlib.metadata.version('school-routine-bot')}")
    settings = get_settings()
    if settings.messenger_tag == "tg":
        from school_routine_bot.main_tg import main
    elif settings.messenger_tag == "vk":
        from school_routine_bot.vk_bot.main_vk import main
    asyncio.run(main())
