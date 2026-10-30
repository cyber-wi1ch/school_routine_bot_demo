from sqlalchemy import inspect, text


def call_inspector(engine, session):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"3. Таблицы в БД: {tables}")

    if "users" in tables:
        print("4. ✓ Таблица 'users' успешно создана!")

        # Показываем структуру
        columns = inspector.get_columns("users")
        print("5. Колонки:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
        print("\nДАННЫЕ:")
        result = session.execute(text("SELECT * FROM users"))

        for row in result:
            # Вариант 1: как кортеж
            print(f"Кортеж: {row}")

    else:
        print("4. ✗ Таблица НЕ создана")
