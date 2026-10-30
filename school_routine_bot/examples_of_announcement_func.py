# async def announce_about_changes(): абсолюнто дргуая работа - надо тянуть юезров из бд теперь.
#     for user, name in matcher.users.items():
#         try:
#             await bot.send_message(
#                 user,
#                 "👋🏻Добрый вечер! У бота изменилась работа кнопки 'Ближайшие дежурства' "
#                 "Чтобы у Вас обновилась версия этой кнопки, "
#                 "пожалуйста, кликните на неё.",
#             )
#             logger.info(f"{name['surname']} have accepted message about new buttons")
#         except ApiTelegramException:
#             logger.error(
#                 f"{user}{name} blocked the bot or are not in bot for another reason"
#             )
#             continue

# DB ANNOUNCEMENT

# async def announce_about_changes():
#     async with get_session() as session:
#         # Для асинхронного SQLAlchemy используйте select и await session.execute
#         from sqlalchemy import select
#         stmt = select(User).where(User.chat_id.is_not(None))
#         result = await session.execute(stmt)
#         users = result.scalars().all()
#
#         for user in users:
#             try:
#                 await bot.send_message(
#                     user.chat_id,
#                     "👋🏻 Спешу сообщить,что теперь наш бот есть ВКонтакте. Прилагаю ссылку и порядок действий, "
#                     "чтобы стать пользователем ВК версии School Routine Bot ( ГДЕ-ТО ТУТ БУДЕТ ССЫЛКА И ПОРЯДОК!!)"
#                 )
#                 logger.info(f"User {user.tg_id} notified")
#             except ApiTelegramException:
#                 logger.error(f"User {user.tg_id} blocked")
