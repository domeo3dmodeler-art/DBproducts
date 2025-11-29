"""
Скрипт для добавления уникальности названия атрибута
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Проверить, есть ли уже уникальный индекс на name
            result = conn.execute(text("PRAGMA index_list(attributes)"))
            indexes = [row[1] for row in result]
            
            # Создать уникальный индекс, если его нет
            if 'ix_attributes_name' not in indexes:
                # Удалить дубликаты перед созданием уникального индекса
                conn.execute(text("""
                    DELETE FROM attributes 
                    WHERE id NOT IN (
                        SELECT MIN(id) 
                        FROM attributes 
                        GROUP BY name
                    )
                """))
                conn.commit()
                
                # Создать уникальный индекс
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_attributes_name ON attributes(name)"))
                conn.commit()
                print('✅ Уникальный индекс на name создан')
            else:
                print('ℹ️ Уникальный индекс на name уже существует')
    except Exception as e:
        print(f'❌ Ошибка: {e}')

