"""
Скрипт для добавления поля unit в таблицу attributes
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Проверить, существует ли колонка
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(attributes)"))
            columns = [row[1] for row in result]
            
            if 'unit' not in columns:
                conn.execute(text("ALTER TABLE attributes ADD COLUMN unit VARCHAR(50)"))
                conn.commit()
                print('✅ Поле unit успешно добавлено в таблицу attributes')
            else:
                print('ℹ️ Поле unit уже существует в таблице attributes')
    except Exception as e:
        print(f'❌ Ошибка: {e}')

