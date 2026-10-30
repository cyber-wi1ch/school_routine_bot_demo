from sqlalchemy import create_engine, text

from school_routine_bot.settings import get_settings

settings = get_settings()
engine = create_engine(settings.database)

with engine.connect() as conn:
    # Проверяем, существует ли уже колонка
    result = conn.execute(text("PRAGMA table_info(users)"))
    columns = [row[1] for row in result]
    if "vk_id" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN vk_id BIGINT"))
        conn.commit()
        print("Column vk_id added successfully")
    else:
        print("Column vk_id already exists")
