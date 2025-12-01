"""
Конфигурация Gunicorn для production
"""
import multiprocessing

# Количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Биндинг
bind = "0.0.0.0:5000"

# Логирование
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Таймауты
timeout = 120
keepalive = 5

# Перезапуск воркеров
max_requests = 1000
max_requests_jitter = 50

# Имя приложения
proc_name = "db_products"

