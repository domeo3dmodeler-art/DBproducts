#!/usr/bin/env python
"""
Скрипт для настройки production окружения
"""
import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Генерация безопасного SECRET_KEY"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Создание .env файла из примера"""
    env_example = Path('env.example')
    env_file = Path('.env')
    
    if env_file.exists():
        print("⚠️  .env файл уже существует. Пропускаю создание.")
        return
    
    if not env_example.exists():
        print("❌ Файл env.example не найден!")
        return
    
    # Прочитать пример
    with open(env_example, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменить SECRET_KEY на сгенерированный
    secret_key = generate_secret_key()
    content = content.replace('your-secret-key-here-change-in-production-min-32-chars', secret_key)
    
    # Записать .env файл
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Создан .env файл с SECRET_KEY: {secret_key[:20]}...")
    print("⚠️  ВАЖНО: Проверьте и обновите остальные переменные окружения!")

def check_directories():
    """Проверка и создание необходимых директорий"""
    directories = [
        'logs',
        'uploads',
        'media/images',
        'media/models',
        'backups',
        'app/static/react'
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Создана директория: {directory}")
        else:
            print(f"✓ Директория существует: {directory}")

def check_requirements():
    """Проверка установленных зависимостей"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_migrate
        import flask_login
        import flask_cors
        import gunicorn
        print("✅ Все основные зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e.name}")
        print("   Установите: pip install -r requirements_production.txt")

if __name__ == '__main__':
    print("🔧 Настройка production окружения...\n")
    
    print("1. Проверка директорий...")
    check_directories()
    print()
    
    print("2. Проверка зависимостей...")
    check_requirements()
    print()
    
    print("3. Создание .env файла...")
    create_env_file()
    print()
    
    print("✅ Настройка завершена!")
    print("\n📋 Следующие шаги:")
    print("   1. Отредактируйте .env файл с правильными значениями")
    print("   2. Настройте PostgreSQL базу данных")
    print("   3. Запустите миграции: flask db upgrade")
    print("   4. Соберите React frontend: cd frontend && npm run build")
    print("   5. Запустите с Gunicorn: gunicorn -c gunicorn_config.py 'app:create_app()'")

