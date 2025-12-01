"""
Скрипт для инициализации production окружения
"""
import os
import secrets
from pathlib import Path

def init_production():
    """Инициализировать production окружение"""
    print("🚀 Инициализация production окружения\n")
    
    # 1. Проверить .env файл
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Создание .env файла из .env.example...")
            content = env_example.read_text()
            
            # Генерировать SECRET_KEY
            secret_key = secrets.token_hex(32)
            content = content.replace('your-secret-key-here-generate-random-string', secret_key)
            
            env_file.write_text(content)
            print(f"✅ .env файл создан")
            print(f"✅ SECRET_KEY сгенерирован: {secret_key[:20]}...")
        else:
            print("❌ .env.example не найден!")
            return False
    else:
        print("ℹ️  .env файл уже существует")
    
    # 2. Создать необходимые папки
    folders = ['logs', 'backups', 'uploads', 'media/images', 'media/models']
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Папка {folder} создана/проверена")
    
    # 3. Проверить права доступа
    print("\n📋 Следующие шаги:")
    print("1. Заполните DATABASE_URL в .env файле (PostgreSQL для production)")
    print("2. Установите FLASK_ENV=production в .env")
    print("3. Установите DEBUG=False в .env")
    print("4. Запустите: python manage.py init_db")
    print("5. Запустите: python scripts/check_security.py")
    
    return True

if __name__ == '__main__':
    init_production()

