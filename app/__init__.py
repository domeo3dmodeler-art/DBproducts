"""
Инициализация Flask приложения
Система сбора и верификации данных о товарах от поставщиков
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

# Инициализация расширений
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    """Фабрика приложения"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
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
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
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
    
    return app

