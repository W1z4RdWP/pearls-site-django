---
name: react-backend
description: Правила написания бэкенда (Django API views) для React-фронтенда. Использовать при создании или редактировании API-представлений для React, добавлении новых эндпоинтов, миграции Django-шаблонов на React API.
---

# Бэкенд для React-фронтенда

## Структура модуля API views

Все API-представления для React расположены в модуле:

```
myproject/apps/api/views/views_frontend/
```

Для **каждого приложения** создаётся отдельный файл по шаблону:

```
views_frontend/
├── views_shop.py        # приложение shop
├── views_users.py       # приложение users
├── views_messenger.py   # приложение messenger
└── ...                  # views_{app-name}.py
```

Имя файла: `views_{app-name}.py`, где `{app-name}` — имя Django-приложения.

## Маршрутизация (urls)

Все эндпоинты для React регистрируются **только** в `myproject/apps/api/urls.py`.

Эндпоинты **обязательно** визуально разделяются по приложениям:
- Пустая строка перед блоком
- Комментарий с названием секции

Пример:

```python
from .views.views_frontend import views_shop as shop_views
from .views.views_frontend import views_users as users_views

urlpatterns = [
    # ...

    # Shop API — данные для фронтенда (магазин работает на React)
    path('shop/products/', shop_views.api_products_list, name='api_shop_products'),
    path('shop/product/details/', shop_views.product_details, name='api_shop_product_details'),

    # Users API — данные пользователей для React
    path('users/transactions/', users_views.api_transactions, name='api_users_transactions'),
]
```

**Важно**: URI существующих эндпоинтов нельзя менять. При миграции с Django-шаблона на React API сохраняй исходные пути.

## Шаблон API-представления

При создании нового файла `views_{app-name}.py` используй следующий шаблон:

```python
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# Импорты моделей конкретного приложения
from {app_name}.models import SomeModel


@login_required
@require_http_methods(["GET"])
def api_some_endpoint(request):
    """API: краткое описание — что возвращает и для чего."""
    # Логика получения данных
    data = {}
    return JsonResponse(data)
```

### Правила написания представлений

1. **JsonResponse** — все представления возвращают `JsonResponse`
2. **Декораторы** — `@login_required` если нужна авторизация, `@require_http_methods` для ограничения HTTP-методов
3. **Пагинация** — использовать `django.core.paginator.Paginator`, возвращать объект pagination в ответе
4. **Фильтрация** — параметры из `request.GET`
5. **Имена функций** — начинаются с `api_` для явной идентификации как API-эндпоинта
6. **Docstring** — обязательный, формат: `"""API: описание."""`
7. **Ошибки** — возвращать `JsonResponse({'error': 'текст'}, status=код)`
8. **Права доступа staff** — проверять через `request.user.is_staff or request.user.is_superuser`

### Стандартный формат пагинации

```python
from django.core.paginator import Paginator

PAGINATE_BY = 20

paginator = Paginator(queryset, PAGINATE_BY)
page_obj = paginator.get_page(page)

response = {
    'items': [...],
    'pagination': {
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    },
}
```

## Миграция Django-шаблона на React API

При переносе Django-шаблона (`.html`) на React:

1. Проанализируй шаблон: какие данные используются (переменные контекста)
2. Найди соответствующий View (CBV/FBV), изучи `get_context_data` / контекст
3. Создай API-представление в `views_{app-name}.py`, которое возвращает те же данные в формате JSON
4. Добавь эндпоинт в `api/urls.py` в секцию соответствующего приложения
5. URI должен быть осмысленным: `{app}/transactions/`, `{app}/products/` и т.д.
6. Шаблон `.html` **не удаляй** до полного перехода на React



# Frontend React — Методология написания кода

## Структура компонентов

Каждый компонент создаётся в отдельной папке внутри `src/components/`. Компоненты, относящиеся к одному Django-приложению, размещают в **общей папке с тем же смысловым именем** (например, страницы и виджеты магазина — в `ShopPage/`, профиля пользователя — в `UsersApp/` и т.д.):

```
src/components/
├── ShopPage/                    # всё, что относится к приложению shop
│   ├── ShopPage.jsx
│   ├── ShopPage.css
│   ├── OrderHistoryPage/
│   │   ├── OrderHistoryPage.jsx
│   │   └── …
│   └── ProductCard/
│       └── …
└── ComponentName/
    ├── ComponentName.jsx   # React-компонент
    └── ComponentName.css   # Стили компонента
```

## Правила написания компонентов

### JSX

1. **Один компонент — один файл.** Экспорт по умолчанию (`export default`).
2. **Именование**: PascalCase для компонентов и файлов (`Header.jsx`, `CourseCarousel.jsx`).
3. **Функциональные компоненты** с хуками (`useState`, `useEffect`, `useCallback`).
4. **Props деструктуризация** в параметрах функции:
   ```jsx
   const Card = ({ title, description, icon }) => { ... }
   ```
5. **Условный рендеринг** через `&&` или тернарный оператор:
   ```jsx
   {isAuthenticated && <ProfileMenu />}
   {items.length > 0 ? <List items={items} /> : <Empty />}
   ```
6. **Списки** рендерятся через `.map()` с уникальным `key`.
7. **Обработчики событий** именуются `handleAction` (например `handleClick`, `handleSubmit`).
8. **Константы и статические данные** выносятся за пределы компонента.

### CSS

1. **Один CSS-файл на компонент.** Импортируется в JSX: `import './ComponentName.css'`.
2. **BEM-подобное именование** с префиксом компонента:
   ```css
   .header { }
   .header__logo { }
   .header__nav-link { }
   .header__nav-link--active { }
   ```
3. **CSS-переменные** из `:root` определяются глобально в `index.css` и используются в компонентах.
4. **Адаптивность** через `@media` запросы внутри CSS-файла компонента.
5. **Никаких inline-стилей** в JSX (кроме динамических значений).

### API

1. Все запросы к бэкенду — через единый модуль `src/api/api.js`.
2. **Разделение API файлов по Django приложениям**: для каждого Django-приложения создаётся отдельный файл API в `src/api/` по шаблону `{app_name}_api.js`. Например:
   - `messenger_api.js` для приложения `messenger`
   - `shop_api.js` для приложения `shop`
   - `users_api.js` для приложения `users`
   
   Каждый такой файл импортирует базовые функции (`request`, `getCSRFToken`, `API_BASE`) из `api.js` и экспортирует функции для работы с конкретным приложением.
3. **Fetch API** с обработкой ошибок.
4. CSRF-токен передаётся через cookie (Django SessionAuthentication).
5. Базовый URL задаётся через Vite proxy (`/api/` → Django backend).

### Общие правила

- **Не дублировать логику.** Общие утилиты — в `src/utils/`.
- **Не хранить секреты** на клиенте.
- **Семантический HTML**: `<header>`, `<main>`, `<footer>`, `<nav>`, `<section>`.
- **Accessibility**: `aria-label`, `alt` для изображений, семантические роли.
- **Загрузка данных**: `useEffect` + `useState` для API-запросов в компонентах.
- **Обработка состояний загрузки**: показывать loading/error/empty состояния.

### Структура проекта

```
frontend/
├── public/                 # Статические файлы
├── src/
│   ├── api/
│   │   └── api.js          # API-клиент
│   ├── components/
│   │   └── ComponentName/
│   │       ├── ComponentName.jsx
│   │       └── ComponentName.css
│   ├── App.jsx             # Корневой компонент с роутингом
│   ├── App.css             # Стили корневого компонента
│   ├── main.jsx            # Точка входа
│   └── index.css           # Глобальные стили и CSS-переменные
├── index.html              # HTML-шаблон
├── vite.config.js          # Конфигурация Vite
└── package.json
```
