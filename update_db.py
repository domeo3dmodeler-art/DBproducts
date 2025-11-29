"""
Скрипт для обновления базы данных
"""
import os
from app import create_app, db
from app.models import *
from app.models.import_history import ImportHistory

app = create_app()

with app.app_context():
    # Удалить старую базу данных
    db_file = 'app.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        print('Старая база данных удалена')
    
    # Создать новую базу данных
    db.create_all()
    print('База данных создана с новой структурой')
    
    # Добавить поле unit в таблицу attributes, если его нет
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Проверить, существует ли колонка
            result = conn.execute(text("PRAGMA table_info(attributes)"))
            columns = [row[1] for row in result]
            if 'unit' not in columns:
                conn.execute(text("ALTER TABLE attributes ADD COLUMN unit VARCHAR(50)"))
                conn.commit()
                print('Поле unit добавлено в таблицу attributes')
    except Exception as e:
        print(f'Ошибка при добавлении поля unit: {e}')
    
    # Создать администратора
    from app.models.user import User
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Администратор',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print('Создан администратор: admin / admin')
    else:
        print('Администратор уже существует')
    
    print('База данных обновлена успешно!')

