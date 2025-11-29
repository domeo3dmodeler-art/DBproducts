"""
Конфигурация приложения
"""
import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()

class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки импорта
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = basedir / 'uploads'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'json'}
    
    # Настройки медиа-файлов
    MEDIA_FOLDER = basedir / 'media'  # Папка для хранения медиа-файлов
    IMAGES_FOLDER = MEDIA_FOLDER / 'images'  # Папка для изображений
    MODELS_FOLDER = MEDIA_FOLDER / 'models'  # Папка для 3D моделей
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB max image size
    MAX_MODEL_SIZE = 50 * 1024 * 1024  # 50MB max 3D model size
    
    # Настройки верификации
    MIN_IMAGE_RESOLUTION = (800, 600)  # Минимальное разрешение изображений
    
    # Pagination
    ITEMS_PER_PAGE = 50

