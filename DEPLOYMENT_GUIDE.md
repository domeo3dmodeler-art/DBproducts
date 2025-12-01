# Руководство по развертыванию в Production

## Предварительные требования

- Python 3.12+
- PostgreSQL 14+
- Node.js 18+ (для сборки frontend)
- Nginx (рекомендуется)
- SSL сертификат

## Шаг 1: Подготовка окружения

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd DB_products2

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements_production.txt

# 4. Запустить скрипт настройки
python scripts/production_setup.py
```

## Шаг 2: Настройка переменных окружения

Отредактируйте `.env` файл:

```bash
# Flask Configuration
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<сгенерированный-ключ>

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/db_products

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_TO_STDOUT=True
```

## Шаг 3: Настройка базы данных

```bash
# 1. Создать базу данных PostgreSQL
createdb db_products

# 2. Применить миграции
export FLASK_APP=run.py
flask db upgrade

# 3. Создать администратора
python manage.py create_user admin admin@example.com admin --admin
```

## Шаг 4: Сборка React Frontend

```bash
cd frontend
npm install
npm run build
```

Собранные файлы будут в `app/static/react/`

## Шаг 5: Настройка Gunicorn

Gunicorn уже настроен в `gunicorn_config.py`. Запуск:

```bash
gunicorn -c gunicorn_config.py 'app:create_app()'
```

Или через systemd (см. ниже).

## Шаг 6: Настройка Nginx

Создайте конфигурацию `/etc/nginx/sites-available/db_products`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Логи
    access_log /var/log/nginx/db_products_access.log;
    error_log /var/log/nginx/db_products_error.log;

    # Максимальный размер загружаемых файлов
    client_max_body_size 50M;

    # Проксирование на Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (если нужно)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Статические файлы
    location /static {
        alias /path/to/DB_products2/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media {
        alias /path/to/DB_products2/media;
        expires 7d;
    }
}
```

Активировать:

```bash
sudo ln -s /etc/nginx/sites-available/db_products /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Шаг 7: Systemd Service

Создайте `/etc/systemd/system/db-products.service`:

```ini
[Unit]
Description=DB Products Gunicorn Application Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/DB_products2
Environment="PATH=/path/to/DB_products2/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/path/to/DB_products2/venv/bin/gunicorn -c gunicorn_config.py 'app:create_app()'
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable db-products
sudo systemctl start db-products
sudo systemctl status db-products
```

## Шаг 8: Мониторинг

### Логи

```bash
# Логи приложения
tail -f logs/app.log

# Логи Gunicorn
tail -f logs/access.log
tail -f logs/error.log

# Логи Nginx
tail -f /var/log/nginx/db_products_access.log
tail -f /var/log/nginx/db_products_error.log
```

### Health Check

```bash
curl https://yourdomain.com/health
```

## Шаг 9: Резервное копирование

Настройте автоматические бэкапы БД:

```bash
# Добавить в crontab
0 2 * * * pg_dump db_products > /path/to/backups/db_products_$(date +\%Y\%m\%d).sql
```

## Безопасность

1. ✅ Используйте сильный SECRET_KEY
2. ✅ Настройте firewall (только необходимые порты)
3. ✅ Используйте HTTPS
4. ✅ Регулярно обновляйте зависимости
5. ✅ Настройте rate limiting
6. ✅ Регулярно делайте бэкапы

## Обновление

```bash
# 1. Остановить сервис
sudo systemctl stop db-products

# 2. Обновить код
git pull

# 3. Обновить зависимости
pip install -r requirements_production.txt

# 4. Применить миграции
flask db upgrade

# 5. Пересобрать frontend (если нужно)
cd frontend && npm run build

# 6. Запустить сервис
sudo systemctl start db-products
```

