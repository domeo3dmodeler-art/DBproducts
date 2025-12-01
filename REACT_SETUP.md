# Настройка React Frontend

## Установка зависимостей

```bash
cd frontend
npm install
```

## Запуск в режиме разработки

### 1. Запустить Flask backend:
```bash
python run.py
```

### 2. В отдельном терминале запустить React dev server:
```bash
cd frontend
npm run dev
```

React приложение будет доступно по адресу: http://localhost:3000

## Сборка для production

```bash
cd frontend
npm run build
```

Собранные файлы будут в `app/static/react/`

После сборки Flask будет автоматически обслуживать React приложение.

## Структура проекта

```
frontend/
├── src/
│   ├── components/     # React компоненты
│   │   └── Layout.jsx
│   ├── pages/          # Страницы приложения
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Products.jsx
│   │   ├── Categories.jsx
│   │   ├── Suppliers.jsx
│   │   ├── Subcategories.jsx
│   │   ├── Attributes.jsx
│   │   └── Import.jsx
│   ├── contexts/      # React Context
│   │   └── AuthContext.jsx
│   ├── services/      # API клиент
│   │   └── api.js
│   ├── App.jsx        # Главный компонент
│   ├── main.jsx        # Точка входа
│   └── index.css      # Глобальные стили
├── package.json
├── vite.config.js     # Конфигурация Vite
└── index.html
```

## Технологии

- **React 18** - UI библиотека
- **React Router 6** - Роутинг
- **TanStack Query** - Управление состоянием сервера
- **Axios** - HTTP клиент
- **Bootstrap 5** - CSS фреймворк
- **Bootstrap Icons** - Иконки
- **Vite** - Сборщик и dev server

## API Интеграция

Frontend работает через прокси на порту 3000 и обращается к Flask API на порту 5000.

Все API запросы идут через `/api/*` и `/auth/*` endpoints.

## Особенности

1. **Аутентификация**: Использует Flask-Login через cookies
2. **CSRF**: Отключен для auth blueprint в DEBUG режиме
3. **Роутинг**: React Router для клиентской навигации
4. **Состояние**: React Query для кэширования и синхронизации данных

