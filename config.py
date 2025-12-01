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
    
    # Логирование
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')


class ProductionConfig(Config):
    """Конфигурация для production"""
    DEBUG = False
    TESTING = False
    
    # Безопасность - будет проверено при создании приложения
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-ME-IN-PRODUCTION'
    
    # База данных - будет проверено при создании приложения
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # CORS настройки для production
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    
    # Настройки сессий
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'  # Только HTTPS
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Логирование
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'True').lower() == 'true'
    
    # Производительность
    pool_size = int(os.environ.get('SQLALCHEMY_POOL_SIZE', '10'))
    pool_recycle = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', '3600'))
    max_overflow = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', '20'))
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': pool_size,
        'pool_recycle': pool_recycle,
        'pool_pre_ping': True,
        'max_overflow': max_overflow
    }


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False


# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
