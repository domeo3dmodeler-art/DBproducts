"""
Инициализация Flask приложения
Система сбора и верификации данных о товарах от поставщиков
"""
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from config import Config

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cors = CORS()

def create_app(config_class=None):
    """Фабрика приложения"""
    from config import config as app_config
    
    # Определить конфигурацию из переменной окружения
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        config_class = app_config.get(env, app_config['default'])
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Отключить кэширование статических файлов в development
    if app.config.get('DEBUG'):
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Проверка production конфигурации
    if config_class.__name__ == 'ProductionConfig':
        if not os.environ.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'CHANGE-ME-IN-PRODUCTION':
            raise ValueError("SECRET_KEY должен быть установлен в переменных окружения для production!")
        if not os.environ.get('DATABASE_URL') or 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            raise ValueError("DATABASE_URL должен быть установлен (PostgreSQL) в переменных окружения для production!")
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Убедиться, что admin пользователь существует (только при первом запуске)
    with app.app_context():
        from app.models.user import User
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_active=True,
                is_admin=True
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Создан пользователь admin по умолчанию')
    
    # Настройка CORS для React frontend
    # В development разрешаем localhost, в production используем переменные окружения
    if app.config.get('DEBUG'):
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    else:
        # В production используем переменные окружения
        cors_origins = app.config.get('CORS_ORIGINS', ["http://localhost:3000"])
        if isinstance(cors_origins, str):
            cors_origins = [origin.strip() for origin in cors_origins.split(',')]
    
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
            "supports_credentials": True,
            "expose_headers": ["Content-Range", "X-Total-Count"]
        },
        r"/auth/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
            "supports_credentials": True
        }
    })
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Настройка user_loader для Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        """Загрузка пользователя по ID"""
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Регистрация Blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Временно отключить CSRF для auth blueprint (только для разработки)
    if app.config.get('DEBUG'):
        csrf.exempt(auth_bp)
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Регистрация API для workflow
    from app.api import workflow as workflow_api
    app.register_blueprint(workflow_api.bp)
    
    from app.import_data import bp as import_bp
    app.register_blueprint(import_bp, url_prefix='/import')
    
    # Регистрация Jinja2 фильтров
    @app.template_filter('status_ru')
    def status_ru_filter(status_value):
        """Перевод статуса на русский язык"""
        status_translations = {
            'draft': 'Черновик',
            'in_progress': 'В работе',
            'to_review': 'На проверке',
            'approved': 'Утвержден',
            'rejected': 'Отклонен',
            'exported': 'Экспортирован'
        }
        return status_translations.get(status_value, status_value)
    
    # Добавить функцию для timestamp в шаблонах
    @app.context_processor
    def inject_timestamp():
        """Добавить timestamp в контекст шаблонов"""
        return {'timestamp': int(time.time())}
    
    # Настройка логирования
    if not app.debug and not app.testing:
        # Создать папку для логов
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Файловый handler с ротацией
        file_handler = RotatingFileHandler(
            logs_dir / 'app.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Уровень логирования из конфигурации
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        file_handler.setLevel(getattr(logging, log_level))
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
        
        # Логирование в stdout для Docker/контейнеров
        if app.config.get('LOG_TO_STDOUT', False):
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
            stream_handler.setLevel(getattr(logging, log_level))
            app.logger.addHandler(stream_handler)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint для мониторинга"""
        try:
            # Проверить подключение к БД
            db.session.execute(db.text('SELECT 1'))
            db_status = 'ok'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return {
            'status': 'ok' if db_status == 'ok' else 'degraded',
            'database': db_status,
            'version': '1.0.0'
        }, 200 if db_status == 'ok' else 503
    
    # Обслуживание React приложения (для production)
    # Это будет обрабатываться после регистрации всех blueprints
    
    return app
