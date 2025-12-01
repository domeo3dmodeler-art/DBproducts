"""
Скрипт для проверки безопасности конфигурации
"""
import os
import sys
from pathlib import Path

# Загрузить переменные из .env файла
def load_env_file():
    """Загрузить переменные из .env файла"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Загрузить .env перед проверкой
load_env_file()

def check_security():
    """Проверить настройки безопасности"""
    issues = []
    warnings = []
    
    # Проверить SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        issues.append("[ERROR] SECRET_KEY не установлен в переменных окружения")
    elif secret_key == 'dev-secret-key-change-in-production':
        issues.append("[ERROR] SECRET_KEY использует значение по умолчанию - измените для production!")
    elif len(secret_key) < 32:
        warnings.append("[WARNING] SECRET_KEY слишком короткий (рекомендуется минимум 32 символа)")
    else:
        print("[OK] SECRET_KEY установлен")
    
    # Проверить DEBUG режим
    debug = os.environ.get('DEBUG', 'False').lower()
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    if flask_env == 'production' and debug == 'true':
        issues.append("[ERROR] DEBUG=True в production окружении!")
    elif flask_env == 'production':
        print("[OK] DEBUG отключен для production")
    
    # Проверить базу данных
    database_url = os.environ.get('DATABASE_URL', '')
    if flask_env == 'production' and 'sqlite' in database_url:
        issues.append("[ERROR] SQLite используется в production - используйте PostgreSQL!")
    elif flask_env == 'production' and 'postgresql' in database_url:
        print("[OK] PostgreSQL настроен для production")
    
    # Проверить .env файл
    env_file = Path('.env')
    if env_file.exists():
        print("[OK] .env файл существует")
        # Проверить, что .env в .gitignore
        gitignore = Path('.gitignore')
        if gitignore.exists():
            content = gitignore.read_text()
            if '.env' in content:
                print("[OK] .env в .gitignore")
            else:
                warnings.append("[WARNING] .env не в .gitignore - добавьте для безопасности")
    else:
        warnings.append("[WARNING] .env файл не найден - создайте из .env.example")
    
    # Проверить логирование
    logs_dir = Path('logs')
    if logs_dir.exists():
        print("[OK] Папка logs существует")
    else:
        warnings.append("[WARNING] Папка logs не существует - будет создана автоматически")
    
    # Вывести результаты
    print("\n" + "="*50)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ БЕЗОПАСНОСТИ")
    print("="*50)
    
    if issues:
        print("\n[CRITICAL] КРИТИЧНЫЕ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"  {issue}")
    
    if warnings:
        print("\n[WARNING] ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not issues and not warnings:
        print("\n[OK] Все проверки безопасности пройдены!")
    
    return len(issues) == 0

if __name__ == '__main__':
    success = check_security()
    sys.exit(0 if success else 1)

