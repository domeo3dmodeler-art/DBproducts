# React Frontend для системы управления товарами

## Установка

```bash
cd frontend
npm install
```

## Запуск в режиме разработки

```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:3000

## Сборка для production

```bash
npm run build
```

Собранные файлы будут в `app/static/react/`

## Структура проекта

```
frontend/
├── src/
│   ├── components/     # React компоненты
│   ├── pages/          # Страницы приложения
│   ├── contexts/      # React Context (Auth)
│   ├── services/      # API клиент
│   ├── App.jsx        # Главный компонент
│   └── main.jsx        # Точка входа
├── package.json
└── vite.config.js     # Конфигурация Vite
```

## Интеграция с Flask

Frontend работает через прокси на порту 3000 и обращается к Flask API на порту 5000.

## Технологии

- React 18
- React Router 6
- TanStack Query (React Query)
- Axios
- Bootstrap 5
- Bootstrap Icons
- Vite

