# ДОКУМЕНТАЦИЯ REST API

## Базовый URL
```
/api
```

## Аутентификация
Большинство эндпоинтов требуют аутентификации через Flask-Login. Используйте сессии для авторизации.

---

## КАТЕГОРИИ ТОВАРОВ

### GET /api/categories
Получить список всех категорий

**Параметры запроса:**
- `include_suppliers` (boolean, опционально) - включить список поставщиков

**Пример:**
```bash
GET /api/categories
GET /api/categories?include_suppliers=true
```

**Ответ:**
```json
[
  {
    "id": 1,
    "code": "plumbing",
    "name": "Сантехника",
    "description": "Категория сантехнических товаров",
    "is_active": true,
    "suppliers_count": 5
  }
]
```

### GET /api/categories/{id}
Получить категорию по ID

**Параметры запроса:**
- `include_suppliers` (boolean, опционально)

### POST /api/categories
Создать новую категорию (требует аутентификации)

**Тело запроса:**
```json
{
  "code": "plumbing",
  "name": "Сантехника",
  "description": "Описание категории",
  "is_active": true
}
```

### PUT /api/categories/{id}
Обновить категорию (требует аутентификации)

**Тело запроса:**
```json
{
  "name": "Новое название",
  "description": "Новое описание",
  "is_active": false
}
```

### DELETE /api/categories/{id}
Удалить категорию (требует аутентификации)

---

## ПОСТАВЩИКИ

### GET /api/suppliers
Получить список поставщиков

**Параметры запроса:**
- `category_id` (integer, опционально) - фильтр по категории
- `include_subcategories` (boolean, опционально)

**Пример:**
```bash
GET /api/suppliers
GET /api/suppliers?category_id=1
GET /api/suppliers?include_subcategories=true
```

### GET /api/suppliers/{id}
Получить поставщика по ID

### POST /api/suppliers
Создать нового поставщика (требует аутентификации)

**Тело запроса:**
```json
{
  "code": "aquame",
  "name": "ООО Акваме",
  "category_id": 1,
  "contact_person": "Иван Иванов",
  "email": "info@aquame.ru",
  "phone": "+7 (495) 123-45-67",
  "address": "Москва, ул. Примерная, д. 1",
  "is_active": true
}
```

### PUT /api/suppliers/{id}
Обновить поставщика (требует аутентификации)

### DELETE /api/suppliers/{id}
Удалить поставщика (требует аутентификации)

---

## ПОДКАТЕГОРИИ

### GET /api/subcategories
Получить список подкатегорий

**Параметры запроса:**
- `supplier_id` (integer, опционально) - фильтр по поставщику
- `include_attributes` (boolean, опционально)
- `include_products` (boolean, опционально)

### GET /api/subcategories/{id}
Получить подкатегорию по ID

### POST /api/subcategories
Создать новую подкатегорию (требует аутентификации)

**Тело запроса:**
```json
{
  "code": "sinks",
  "name": "Раковины",
  "supplier_id": 1,
  "description": "Подкатегория раковин",
  "is_active": true
}
```

### PUT /api/subcategories/{id}
Обновить подкатегорию (требует аутентификации)

### DELETE /api/subcategories/{id}
Удалить подкатегорию (требует аутентификации)

---

## ТОВАРЫ

### GET /api/products
Получить список товаров

**Параметры запроса:**
- `subcategory_id` (integer, опционально) - фильтр по подкатегории
- `status` (string, опционально) - фильтр по статусу (draft, in_progress, to_review, approved, rejected, exported)
- `include_attributes` (boolean, опционально)
- `include_verification` (boolean, опционально)

**Пример:**
```bash
GET /api/products
GET /api/products?subcategory_id=1&status=approved
GET /api/products?include_attributes=true&include_verification=true
```

### GET /api/products/{id}
Получить товар по ID

**Параметры запроса:**
- `include_attributes` (boolean, по умолчанию true)
- `include_verification` (boolean, по умолчанию true)
- `include_history` (boolean, опционально)

### POST /api/products/{id}/verify
Запустить верификацию товара (требует аутентификации)

**Пример:**
```bash
POST /api/products/1/verify
```

**Ответ:**
```json
{
  "id": 1,
  "product_id": 1,
  "completeness_score": 85,
  "quality_score": 90,
  "media_score": 75,
  "overall_score": 85,
  "verified_at": "2024-01-15T10:30:00",
  "issues": [...]
}
```

### PUT /api/products/{id}/status
Изменить статус товара (требует аутентификации)

**Тело запроса:**
```json
{
  "status": "approved",
  "comment": "Товар проверен и одобрен"
}
```

**Доступные статусы:**
- `draft` - Черновик
- `in_progress` - В работе
- `to_review` - На проверке
- `approved` - Утвержден
- `rejected` - Отклонен
- `exported` - Экспортирован

### GET /api/products/{id}/versions
Получить список версий товара

**Ответ:**
```json
[
  {
    "id": 1,
    "product_id": 1,
    "version_number": 1,
    "data": {...},
    "created_at": "2024-01-15T10:00:00",
    "created_by": "admin",
    "comment": "Первая версия"
  }
]
```

### POST /api/products/{id}/versions
Создать версию товара (требует аутентификации)

**Тело запроса:**
```json
{
  "comment": "Описание изменений"
}
```

---

## АТРИБУТЫ

### GET /api/attributes
Получить список всех атрибутов

**Параметры запроса:**
- `include_values` (boolean, опционально) - включить варианты значений для SELECT

### GET /api/attributes/{id}
Получить атрибут по ID

---

## КОДЫ ОТВЕТОВ

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс успешно создан
- `400 Bad Request` - Неверный запрос (ошибки валидации)
- `404 Not Found` - Ресурс не найден
- `500 Internal Server Error` - Внутренняя ошибка сервера

---

## ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Создание категории
```bash
curl -X POST http://localhost:5000/api/categories \
  -H "Content-Type: application/json" \
  -d '{
    "code": "plumbing",
    "name": "Сантехника",
    "description": "Категория сантехнических товаров",
    "is_active": true
  }'
```

### Получение товаров с верификацией
```bash
curl http://localhost:5000/api/products?include_verification=true
```

### Запуск верификации товара
```bash
curl -X POST http://localhost:5000/api/products/1/verify
```

### Изменение статуса товара
```bash
curl -X PUT http://localhost:5000/api/products/1/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "comment": "Товар проверен"
  }'
```

---

**Дата создания:** 2024

