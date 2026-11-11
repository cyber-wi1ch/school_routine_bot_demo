# async def announce_about_changes(): Needs reworking: load users from the database now.
#     for user, name in matcher.users.items():
#         try:
#             await bot.send_message(
#                 user,
#                 "👋🏻Good evening! The bot's 'Upcoming duties' button has changed. "
#                 "To refresh the button, "
#                 "please click it.",
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
#         # For async SQLAlchemy, use select and await session.execute
#         from sqlalchemy import select
#         stmt = select(User).where(User.chat_id.is_not(None))
#         result = await session.execute(stmt)
#         users = result.scalars().all()
#
#         for user in users:
#             try:
#                 await bot.send_message(
#                     user.chat_id,
#                     "👋🏻 Our bot is now available on VK. Here are the link and instructions "
#                     "for joining the VK version of School Routine Bot (ADD THE LINK AND STEPS HERE)"
#                 )
#                 logger.info(f"User {user.tg_id} notified")
#             except ApiTelegramException:
#                 logger.error(f"User {user.tg_id} blocked")
