from sqlalchemy import text


def make_telegram_id_nullable(engine):
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))

        # Recreate the table with a nullable telegram_id
        conn.execute(
            text(
                """
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                surname VARCHAR(30) NOT NULL,
                name VARCHAR(30) NOT NULL,
                by_father_name VARCHAR(30) NOT NULL,
                telegram_id BIGINT,
                vk_id BIGINT,
                UNIQUE(telegram_id),
                UNIQUE(vk_id)
            )
        """
            )
        )

        # Copy the data
        conn.execute(text("INSERT INTO users_new SELECT * FROM users"))

        # Replace the old table
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))
        conn.execute(text("PRAGMA foreign_keys=ON"))

        conn.commit()
