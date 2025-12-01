# Руководство по развертыванию

## 🚀 Быстрый старт для Production

### 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python и зависимости
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx -y

# Установить Gunicorn
pip3 install gunicorn
```

### 2. Настройка базы данных PostgreSQL

```bash
# Войти в PostgreSQL
sudo -u postgres psql

# Создать базу данных и пользователя
CREATE DATABASE db_products;
CREATE USER dbuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE db_products TO dbuser;
\q
```

### 3. Настройка приложения

```bash
# Клонировать репозиторий
git clone https://github.com/domeo3dmodeler-art/DBproducts.git
cd DBproducts

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env
nano .env  # Заполнить значения

# Инициализировать базу данных
flask db upgrade
python update_db.py
```

### 4. Запуск с Gunicorn

```bash
# Запустить приложение
gunicorn -c gunicorn_config.py "run:app"

# Или с системным сервисом (systemd)
sudo nano /etc/systemd/system/db-products.service
```

Содержимое файла сервиса:
```ini
[Unit]
Description=DB Products Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/DBproducts
Environment="PATH=/path/to/DBproducts/venv/bin"
ExecStart=/path/to/DBproducts/venv/bin/gunicorn -c gunicorn_config.py "run:app"

[Install]
WantedBy=multi-user.target
```

```bash
# Активировать сервис
sudo systemctl enable db-products
sudo systemctl start db-products
```

### 5. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/db-products
```

Конфигурация Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/DBproducts/app/static;
    }

    location /media {
        alias /path/to/DBproducts/media;
    }
}
```

```bash
# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/db-products /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Настройка SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 7. Настройка резервного копирования

```bash
# Добавить в crontab
crontab -e

# Резервное копирование каждый день в 2:00
0 2 * * * cd /path/to/DBproducts && /path/to/venv/bin/python backup.py
```

## 📋 Чеклист развертывания

- [ ] Сервер настроен
- [ ] PostgreSQL установлен и настроен
- [ ] Приложение установлено
- [ ] .env файл создан и заполнен
- [ ] База данных инициализирована
- [ ] Gunicorn настроен
- [ ] Systemd сервис создан
- [ ] Nginx настроен
- [ ] SSL сертификат установлен
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен
- [ ] Тестирование выполнено

## 🔍 Проверка работы

```bash
# Проверить статус сервиса
sudo systemctl status db-products

# Проверить логи
sudo journalctl -u db-products -f

# Проверить Nginx
sudo nginx -t
sudo systemctl status nginx
```

## 🆘 Устранение неполадок

### Приложение не запускается
1. Проверить логи: `sudo journalctl -u db-products -n 50`
2. Проверить .env файл
3. Проверить права доступа к файлам

### База данных не подключается
1. Проверить DATABASE_URL в .env
2. Проверить доступность PostgreSQL
3. Проверить права пользователя БД

### Nginx не работает
1. Проверить конфигурацию: `sudo nginx -t`
2. Проверить логи: `sudo tail -f /var/log/nginx/error.log`
3. Проверить, что Gunicorn запущен

