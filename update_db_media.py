"""
Скрипт для создания таблицы product_media в базе данных
"""
from app import create_app, db
from app.models.product_media import ProductMedia
from pathlib import Path
import os

app = create_app()

with app.app_context():
    try:
        # Создать таблицу
        db.create_all()
        
        # Создать папки для медиа-файлов
        from config import Config
        os.makedirs(Config.IMAGES_FOLDER, exist_ok=True)
        os.makedirs(Config.MODELS_FOLDER, exist_ok=True)
        
        print('✅ Таблица product_media создана')
        print('✅ Папки для медиа-файлов созданы')
    except Exception as e:
        print(f'❌ Ошибка: {e}')

