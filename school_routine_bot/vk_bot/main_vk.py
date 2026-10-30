import asyncio
import random
import sys
from datetime import time
from typing import Any, Coroutine

from loguru import logger
from vkbottle import Bot, LoopWrapper

from school_routine_bot.db_files.db_create import create_database
from school_routine_bot.db_files.db_models import Admin
from school_routine_bot.google_sheets_morning_duty import (
    add_morning_duty_export_tasks,
    clear_students_cache,
)
from school_routine_bot.google_sheets_polling import GoogleSheetsPolling
from school_routine_bot.notify_all_school_scheduler_impl import scheduler
from school_routine_bot.roles import add_user_to_certain_db_model
from school_routine_bot.scheduler_organizer import SchedulerOrganizer
from school_routine_bot.settings import Settings, get_settings
from school_routine_bot.setup_logging import setup_logger
from school_routine_bot.sqlite_backup import create_backup
from school_routine_bot.vk_bot.vk_client import (
    clean_up_html_symbols,
    matcher,
    setup_handlers,
    vk_api,
)


def create_scheduler(
    admin_base: str, page_title: str, settings: Settings
) -> Coroutine[Any, Any, None]:
    schedular_organizer = SchedulerOrganizer(page_title, matcher, admin_base, notify)
    data_for_scheduler = GoogleSheetsPolling(
        page_title, settings.credentials_for_tables_file, settings.table_url
    ).get_the_updated_worksheet(schedular_organizer.handle_new_data)
    return data_for_scheduler


async def notify(
    person_id, message, parse_mode=None
):  # mb, we can delete api, however we call vk_bot bellow in main - how should it be solved?
    try:
        user = matcher.get_user_full_name_by_id(person_id)
        message = clean_up_html_symbols(message)
        await vk_api.messages.send(
            user_id=person_id,
            message=message,
            random_id=random.randint(1, 2**31),
            dont_parse_links=None,
        )
        logger.success(f"Notified in VK: {user} {person_id} {message}")
        return True
    except Exception:
        logger.exception(f"Не удалось отправить уведомление VK получателю {person_id}")
        return False


@logger.catch(onerror=lambda _: sys.exit(1))
async def main():
    settings = get_settings()

    setup_logger(
        secrets=(
            settings.bot_token.get_secret_value(),
            settings.vk_bot_token.get_secret_value(),
        )
    )

    vk_bot = Bot(
        token=settings.vk_bot_token.get_secret_value(),
        loop_wrapper=LoopWrapper(loop=asyncio.get_running_loop()),
    )
    vk_bot.loop_wrapper._running = True
    #  NOTE This is a crutch to make vkbottle think that its loop_wrapper
    #  already running to avoid it to start it again.
    #  It works just because we pass our running event loop inside the bot during creation,
    #  and it is failing without explicit vk_bot.loop_wrapper._running = True
    #  This behavior may be changed in the future vkbottle versions, so it may crash some day during vkbottle update

    setup_handlers(vk_bot)

    create_database(settings.database)
    add_user_to_certain_db_model(Admin, settings.admins)

    scheduler.add_daily_task(
        target_time=time(3, 5),
        func=lambda: asyncio.to_thread(
            create_backup,
            settings.database.removeprefix("sqlite:///"),
        ),
    )

    # await announce_about_changes()  # - a func to say something to every user,
    # needed sometime especially when we changed bot work
    scheduler.add_daily_task(
        target_time=time(23, 0),
        func=clear_students_cache,
    )

    add_morning_duty_export_tasks(
        scheduler=scheduler,
        export_times=[
            time(10, 40),
            time(18, 10),
            time(0, 40),
        ],
    )
    logger.info("Retry and export tasks started")

    await asyncio.gather(
        scheduler.start(),
        create_scheduler("admin_base_1.json", "Запись на дежурства", settings),
        vk_bot.run_polling(),
    )


if __name__ == "__main__":
    asyncio.run(main())
