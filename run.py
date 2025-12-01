"""
Точка входа приложения
"""
import os
from app import create_app
from config import config

# Определить конфигурацию из переменной окружения
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config.get(config_name, config['default']))

if __name__ == '__main__':
    # Для production используйте WSGI сервер (Gunicorn/uWSGI)
    # Не запускайте через python run.py в production!
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'  # По умолчанию DEBUG=True для разработки
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
