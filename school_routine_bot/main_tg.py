import asyncio
import sys
from datetime import time
from typing import Any, Coroutine

from loguru import logger
from telebot.asyncio_helper import ApiTelegramException

from school_routine_bot.db_files.db_create import create_database
from school_routine_bot.db_files.db_models import Admin
from school_routine_bot.google_sheets_morning_duty import (
    add_morning_duty_export_tasks,
    clear_students_cache,
)
from school_routine_bot.google_sheets_polling import (
    GoogleSheetsPolling,
)
from school_routine_bot.notify_all_school_scheduler_impl import (
    scheduler,
)
from school_routine_bot.roles import add_user_to_certain_db_model
from school_routine_bot.scheduler_organizer import SchedulerOrganizer
from school_routine_bot.settings import Settings, get_settings
from school_routine_bot.setup_logging import setup_logger
from school_routine_bot.sqlite_backup import create_backup
from school_routine_bot.tg_client import (
    bot,
    matcher,
    update_users_states,
)


def create_scheduler(
    admin_base: str, page_title: str, settings: Settings
) -> Coroutine[Any, Any, None]:
    schedular_organizer = SchedulerOrganizer(page_title, matcher, admin_base, notify)
    data_for_scheduler = GoogleSheetsPolling(
        page_title, settings.credentials_for_tables_file, settings.table_url
    ).get_the_updated_worksheet(schedular_organizer.handle_new_data)
    return data_for_scheduler


async def notify(person_id, message, parse_mode=None):
    try:
        user = matcher.get_user_full_name_by_id(person_id)
        logger.warning("Tried to send message!")
        if parse_mode:
            await bot.send_message(person_id, message, parse_mode)
        else:
            await bot.send_message(person_id, message)

        logger.success(
            f"Notified: {user} {person_id}: {message}",
        )
        return True

    except ApiTelegramException as e:
        logger.error(e)
        return False

    except Exception:
        logger.exception(f"Не удалось отправить уведомление получателю {person_id}")
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

    create_database(settings.database)
    add_user_to_certain_db_model(Admin, settings.admins)

    scheduler.add_daily_task(
        target_time=time(3, 0),
        func=lambda: asyncio.to_thread(
            create_backup,
            settings.database.removeprefix("sqlite:///"),
        ),
    )

    update_users_states()
    # call_inspector(engine, get_session())  # wrap into with
    #
    # await announce_about_changes()
    scheduler.add_daily_task(
        target_time=time(23, 0),
        func=clear_students_cache,
    )

    add_morning_duty_export_tasks(
        scheduler=scheduler,
        export_times=[
            time(10, 30),
            time(18, 0),
            time(0, 30),
        ],
    )
    logger.info("Retry and export tasks started")

    await asyncio.gather(
        scheduler.start(),
        create_scheduler("admin_base_1.json", "Запись на дежурства", settings),
        bot.polling(none_stop=True),
    )


if __name__ == "__main__":
    asyncio.run(main())
