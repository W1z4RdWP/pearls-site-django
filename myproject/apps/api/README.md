# Приложение API - REST API для интеграции с внешними сервисами

## Обзор

Приложение `api` предоставляет REST API endpoints для интеграции Django-приложения с внешними сервисами, включая Telegram боты, мобильные приложения и другие системы. Это центральный модуль для API-интеграций платформы.

## Архитектура

### Структура приложения

```
api/
├── models.py                    # Модели данных (если требуются)
├── views.py                     # API представления
├── urls.py                      # URL маршруты
├── apps.py                      # Конфигурация приложения
├── tests.py                     # Тесты
├── serializers.py               # Сериализаторы (если используется DRF)
├── permissions.py               # Кастомные разрешения
└── utils.py                     # Вспомогательные функции
```

## Модели данных

В текущей версии приложение не содержит собственных моделей, а использует существующие модели из других приложений (User, Profile).

## API Endpoints

### Telegram Integration

#### POST /api/telegram/register/
**Функция:** Автоматическая регистрация пользователей из Telegram бота

**Метод:** `POST`

**Разрешения:** `AllowAny` (публичный доступ)

**Параметры запроса:**
```json
{
    "first_name": "Иван",
    "last_name": "Петров", 
    "middle_name": "Сергеевич",
    "phone": "+79001234567",
    "email": "ivan.petrov@example.com",
    "password": "secure_password_123"
}
```

**Обязательные поля:**
- `first_name` - Имя пользователя
- `last_name` - Фамилия пользователя
- `phone` - Номер телефона
- `email` - Email адрес (используется как username)
- `password` - Пароль для входа

**Опциональные поля:**
- `middle_name` - Отчество пользователя

**Ответы:**

**Успешная регистрация (201):**
```json
{
    "success": true,
    "user_id": 123,
    "message": "Пользователь успешно зарегистрирован"
}
```

**Ошибка валидации (400):**
```json
{
    "error": "Поле email обязательно"
}
```

**Пользователь уже существует (400):**
```json
{
    "error": "Пользователь с таким email уже существует"
}
```

**Ошибка базы данных (400):**
```json
{
    "error": "Ошибка базы данных: [детали ошибки]"
}
```

**Внутренняя ошибка (500):**
```json
{
    "error": "Неожиданная ошибка: [детали ошибки]"
}
```

## Представления (Views)

### telegram_register
**Функция:** `telegram_register(request)`
**URL:** `/api/telegram/register/`
**Метод:** `POST`

**Функциональность:**
- Валидация обязательных полей
- Проверка уникальности email и username
- Создание пользователя Django
- Автоматическое создание профиля пользователя
- Обновление профиля дополнительными данными

**Логика работы:**
1. Валидация входных данных
2. Проверка существования пользователя с таким email
3. Создание пользователя в транзакции
4. Создание/обновление профиля пользователя
5. Возврат результата операции

**Безопасность:**
- CSRF защита отключена для API endpoints
- Валидация всех входных данных
- Транзакционная безопасность при создании пользователя

## URL маршруты

### Основные маршруты
- `/api/telegram/register/` - Регистрация пользователей из Telegram

### Включение в основной проект
```python
# myproject/urls.py
path('api/', include('apps.api.urls'), name='api'),
```

## Интеграция с Telegram ботом

### Пример использования в Python

```python
import requests
import json

def register_user_from_telegram(user_data):
    """
    Регистрация пользователя на сайте через API
    
    Args:
        user_data (dict): Данные пользователя из Telegram бота
        
    Returns:
        dict: Результат регистрации
    """
    url = "https://yoursite.com/api/telegram/register/"
    
    payload = {
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"], 
        "middle_name": user_data.get("middle_name", ""),
        "phone": user_data["phone"],
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return {
            "success": response.status_code == 201,
            "status_code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Ошибка сети: {str(e)}"
        }
```

### Пример использования в JavaScript

```javascript
async function registerUserFromTelegram(userData) {
    const url = '/api/telegram/register/';
    
    const payload = {
        first_name: userData.first_name,
        last_name: userData.last_name,
        middle_name: userData.middle_name || '',
        phone: userData.phone,
        email: userData.email,
        password: userData.password
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('Пользователь успешно зарегистрирован:', result);
            return { success: true, data: result };
        } else {
            console.error('Ошибка регистрации:', result);
            return { success: false, error: result.error };
        }
    } catch (error) {
        console.error('Ошибка сети:', error);
        return { success: false, error: error.message };
    }
}
```

## Тестирование API

### Используя curl

```bash
# Успешная регистрация
curl -X POST http://localhost:8000/api/telegram/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Алексей",
    "last_name": "Козлов",
    "middle_name": "Дмитриевич",
    "phone": "+79005554433",
    "email": "alexey.kozlov@example.com",
    "password": "my_password_2024"
  }'

# Тест без обязательного поля
curl -X POST http://localhost:8000/api/telegram/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Анна",
    "last_name": "Морозова",
    "phone": "+79007778899",
    "password": "password123"
  }'
```

### Используя Python requests

```python
import requests

def test_api():
    url = "http://localhost:8000/api/telegram/register/"
    
    # Тест 1: Успешная регистрация
    data1 = {
        "first_name": "Мария",
        "last_name": "Сидорова",
        "middle_name": "Александровна",
        "phone": "+79009876543",
        "email": "maria.sidorova@example.com",
        "password": "secure_password_123"
    }
    
    response1 = requests.post(url, json=data1)
    print(f"Тест 1 - Статус: {response1.status_code}")
    print(f"Ответ: {response1.json()}")
    
    # Тест 2: Дублирование email
    response2 = requests.post(url, json=data1)
    print(f"Тест 2 - Статус: {response2.status_code}")
    print(f"Ответ: {response2.json()}")
    
    # Тест 3: Отсутствует обязательное поле
    data3 = {
        "first_name": "Дмитрий",
        "last_name": "Петров",
        "phone": "+79001112233",
        "password": "password123"
    }
    
    response3 = requests.post(url, json=data3)
    print(f"Тест 3 - Статус: {response3.status_code}")
    print(f"Ответ: {response3.json()}")

if __name__ == "__main__":
    test_api()
```

## Безопасность

### Аутентификация и авторизация
- API endpoints могут быть защищены различными способами аутентификации
- Текущий endpoint `/telegram/register/` публичный для интеграции с ботами
- Возможность добавления API ключей или токенов для других endpoints

### Валидация данных
- Проверка обязательных полей
- Валидация формата email
- Проверка уникальности пользователей
- Санитизация входных данных

### CSRF защита
- CSRF защита отключена для API endpoints
- Использование токенов или других методов аутентификации

## Расширение функциональности

### Добавление новых API endpoints

1. **Создать представление в `views.py`:**
```python
@api_view(['POST'])
@permission_classes([AllowAny])
def new_endpoint(request):
    # Логика endpoint
    pass
```

2. **Добавить URL в `urls.py`:**
```python
urlpatterns = [
    path('new-endpoint/', views.new_endpoint, name='new_endpoint'),
]
```

3. **Добавить тесты в `tests.py`**

### Интеграция с другими сервисами

**WhatsApp Business API:**
```python
@api_view(['POST'])
def whatsapp_register(request):
    # Логика регистрации через WhatsApp
    pass
```

**SMS Gateway:**
```python
@api_view(['POST'])
def sms_verification(request):
    # Логика верификации через SMS
    pass
```

**VK API:**
```python
@api_view(['POST'])
def vk_register(request):
    # Логика регистрации через VK
    pass
```

## Мониторинг и логирование

### Логирование API запросов
```python
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def telegram_register(request):
    logger.info(f"Telegram registration attempt for email: {request.data.get('email')}")
    # ... логика регистрации
```

### Метрики использования
- Количество успешных регистраций
- Количество ошибок по типам
- Время ответа API
- Популярность различных endpoints

## Развертывание

### Требования
- Django 3.2+
- Django REST Framework
- PostgreSQL/MySQL
- Nginx/Apache для production

### Настройки
- Настройка CORS для cross-origin запросов
- Конфигурация rate limiting
- Настройка мониторинга и логирования

### Production рекомендации
- Использование HTTPS
- Настройка rate limiting
- Мониторинг производительности
- Резервное копирование данных

## Тестирование

### Unit тесты
```python
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class TelegramRegisterAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/telegram/register/'
    
    def test_successful_registration(self):
        data = {
            "first_name": "Тест",
            "last_name": "Пользователь",
            "phone": "+79001234567",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=data['email']).exists())
    
    def test_duplicate_email(self):
        # Создаем пользователя
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="pass123"
        )
        
        data = {
            "first_name": "Тест",
            "last_name": "Пользователь",
            "phone": "+79001234567",
            "email": "existing@example.com",
            "password": "testpass123"
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

## Поддержка и документация

### Дополнительные ресурсы
- [Django REST Framework документация](https://www.django-rest-framework.org/)
- [Django API документация](https://docs.djangoproject.com/en/stable/topics/http/views/)
- [REST API best practices](https://restfulapi.net/)

### Контакты
- Вопросы по разработке: [Владислав Кузнецов](https://t.me/w1z4rdWP)
- Issues и feature requests: GitHub repository

### Roadmap
- [ ] Добавление аутентификации по API ключам
- [ ] Rate limiting для API endpoints
- [ ] Swagger/OpenAPI документация
- [ ] Webhook поддержка
- [ ] Интеграция с другими мессенджерами
- [ ] API версионирование
- [ ] Кэширование ответов
- [ ] Метрики и мониторинг
