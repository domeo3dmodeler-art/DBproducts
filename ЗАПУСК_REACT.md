# Запуск React Frontend

## Быстрый старт

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Запуск в режиме разработки

**Терминал 1 - Flask Backend:**
```bash
python run.py
```

**Терминал 2 - React Frontend:**
```bash
cd frontend
npm run dev
```

React приложение будет доступно по адресу: **http://localhost:3000**

Flask API будет доступно по адресу: **http://localhost:5000**

### 3. Сборка для production

```bash
cd frontend
npm run build
```

После сборки файлы будут в `app/static/react/` и Flask будет автоматически обслуживать React приложение.

## Структура

- `frontend/src/components/` - React компоненты
- `frontend/src/pages/` - Страницы приложения
- `frontend/src/contexts/` - React Context (Auth)
- `frontend/src/services/` - API клиент

## API Endpoints

- `/api/dashboard/stats` - Статистика дашборда
- `/api/categories` - Категории
- `/api/suppliers` - Поставщики
- `/api/products` - Товары
- `/auth/login` - Вход (поддерживает JSON)
- `/auth/check` - Проверка аутентификации
- `/auth/logout` - Выход

## Особенности

1. **Аутентификация**: Использует Flask-Login через cookies
2. **Роутинг**: React Router для клиентской навигации
3. **Состояние**: React Query для кэширования данных
4. **Стили**: Bootstrap 5 + Bootstrap Icons

