"""
Конфигурация для pytest
"""
import pytest
import os
import tempfile
from pathlib import Path
from app import create_app, db
from app.models.user import User
from config import Config


class TestConfig(Config):
    """Конфигурация для тестов"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # Отключаем CSRF для тестов
    
    # Тестовые папки
    UPLOAD_FOLDER = Path(tempfile.mkdtemp())
    MEDIA_FOLDER = Path(tempfile.mkdtemp())
    IMAGES_FOLDER = MEDIA_FOLDER / 'images'
    MODELS_FOLDER = MEDIA_FOLDER / 'models'


@pytest.fixture(scope='session')
def app():
    """Создание приложения для тестов"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Клиент для тестирования"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """CLI runner для тестирования"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Сессия базы данных для тестов"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def auth_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.set_password('testpass123')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def auth_headers(client, auth_user):
    """Заголовки для авторизованных запросов"""
    # Логинимся
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    
    # Получаем сессию
    with client.session_transaction() as sess:
        return {'Cookie': client.cookie_jar._cookies}


@pytest.fixture(scope='function')
def logged_in_client(client, auth_user):
    """Клиент с авторизованным пользователем"""
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    return client

