# Приложение Tech Support - Система технической поддержки

## Обзор

Приложение `tech_support` предоставляет полнофункциональную систему технической поддержки для платформы обучения. Включает создание тикетов, управление ими, систему комментариев, вложений и отчетности для администраторов.

## Архитектура

### Структура приложения

```
tech_support/
├── models.py                    # Модели данных (Ticket, TicketStatus, TicketPriority, etc.)
├── views.py                     # Представления (CreateView, DetailView, ListView)
├── urls.py                      # URL маршруты
├── forms.py                     # Формы для создания и управления тикетами
├── apps.py                      # Конфигурация приложения
├── tests.py                     # Тесты
├── admin.py                     # Админ-панель
├── templates/                   # HTML шаблоны
│   ├── tech_support/
│   │   ├── support_chat.html    # Форма создания тикета
│   │   ├── ticket_detail.html   # Детальный просмотр тикета
│   │   ├── ticket_list.html     # Список тикетов для админов
│   │   ├── my_ticket_list.html  # Список тикетов пользователя
│   │   ├── staff_dashboard.html # Дашборд для сотрудников
│   │   └── ticket_reports.html  # Отчеты по тикетам
└── templatetags/                # Кастомные теги шаблонов
    └── tech_support_extras.py
```

## Модели данных

### TicketCategory
**Функция:** Категории тикетов для классификации обращений

**Поля:**
- `name` - Название категории (CharField, max_length=100)
- `description` - Описание категории (TextField)
- `icon` - Иконка FontAwesome (CharField, max_length=50, default='fas fa-question')

### TicketPriority
**Функция:** Уровни приоритета тикетов с временными рамками

**Поля:**
- `name` - Название приоритета (CharField, max_length=100)
- `level` - Уровень приоритета (IntegerField, unique=True)
- `response_time_hours` - Время ответа в часах (IntegerField)
- `color` - Цвет для отображения (CharField, max_length=7, default='#007bff')

### TicketStatus
**Функция:** Статусы тикетов (активные/закрытые)

**Поля:**
- `name` - Название статуса (CharField, max_length=50)
- `color` - Цвет для отображения (CharField, max_length=7, default='#6c757d')
- `is_active` - Активный статус (BooleanField, default=True)

### Ticket
**Функция:** Основная модель тикета

**Поля:**
- `ticket_number` - Уникальный номер тикета (CharField, max_length=20, unique=True)
- `title` - Заголовок проблемы (CharField, max_length=200)
- `description` - Описание проблемы (TextField)
- `ticket_type` - Тип тикета (CharField, choices=TICKET_TYPES)
- `category` - Категория (ForeignKey to TicketCategory)
- `priority` - Приоритет (ForeignKey to TicketPriority)
- `status` - Статус (ForeignKey to TicketStatus)
- `created_by` - Создатель (ForeignKey to User)
- `assigned_to` - Исполнитель (ForeignKey to User, null=True, blank=True)
- `created_at` - Дата создания (DateTimeField, auto_now_add=True)
- `updated_at` - Дата обновления (DateTimeField, auto_now=True)
- `resolved_at` - Дата решения (DateTimeField, null=True, blank=True)
- `deadline` - Дедлайн (DateTimeField, null=True, blank=True)
- `is_anonymous` - Анонимный тикет (BooleanField, default=False)
- `rating` - Оценка решения (IntegerField, 1-5, null=True, blank=True)
- `student_feedback` - Отзыв студента (TextField, blank=True)

**Типы тикетов:**
- `academic` - Учебные вопросы
- `technical` - Технические проблемы
- `administrative` - Административные запросы
- `suggestions` - Предложения/замечания
- `consultation` - Запросы на консультацию

### TicketAttachment
**Функция:** Вложения к тикетам

**Поля:**
- `ticket` - Связанный тикет (ForeignKey to Ticket)
- `file` - Файл (FileField, upload_to='ticket_attachments/')
- `filename` - Оригинальное имя файла (CharField, max_length=255)
- `uploaded_at` - Дата загрузки (DateTimeField, auto_now_add=True)

### TicketComment
**Функция:** Комментарии к тикетам

**Поля:**
- `ticket` - Связанный тикет (ForeignKey to Ticket)
- `author` - Автор комментария (ForeignKey to User)
- `content` - Содержание (TextField)
- `is_internal` - Внутренний комментарий (BooleanField, default=False)
- `created_at` - Дата создания (DateTimeField, auto_now_add=True)

## API Endpoints

### Создание тикета

#### POST /tech_support/chat/
**Функция:** Создание нового тикета поддержки

**Метод:** `POST`

**Разрешения:** Требуется аутентификация

**Параметры запроса:**
```json
{
  "title": "Не открывается урок №3",
  "description": "При попытке открыть урок появляется ошибка 500",
  "attachments": "file" // Опционально, multipart/form-data
}
```

**Обязательные поля:**
- `title` - Заголовок проблемы (минимум 5 символов)
- `description` - Описание проблемы (минимум 10 символов)

**Опциональные поля:**
- `attachments` - Файл вложения (максимум 10MB, форматы: JPG, PNG, PDF, DOC, TXT, LOG)

**Ответы:**

**Успешное создание (302):**
- Редирект на страницу созданного тикета

**Ошибка валидации (200):**
- Возврат формы с ошибками валидации

### Просмотр тикета

#### GET /tech_support/ticket/<int:pk>/
**Функция:** Детальный просмотр тикета

**Метод:** `GET`

**Разрешения:** 
- Автор тикета
- Сотрудники поддержки (если тикет свободен или назначен им)
- Суперпользователи

**Ответы:**

**Успешный просмотр (200):**
- HTML страница с детальной информацией о тикете
- Комментарии и вложения
- Формы для обновления (для сотрудников)

**Доступ запрещен (403):**
- HTML страница с ошибкой доступа

### Список тикетов

#### GET /tech_support/tickets/
**Функция:** Список всех тикетов (для сотрудников)

**Метод:** `GET`

**Разрешения:** Требуется статус staff или superuser

**Параметры запроса:**
- `status` - Фильтр по статусу (id или название)
- `priority` - Фильтр по приоритету (id или уровень)
- `ticket_type` - Фильтр по типу
- `search` - Поиск по заголовку/описанию/номеру
- `date_from` - Фильтр с даты (YYYY-MM-DD)
- `date_to` - Фильтр до даты (YYYY-MM-DD)

#### GET /tech_support/my-tickets/
**Функция:** Список тикетов пользователя

**Метод:** `GET`

**Разрешения:** Требуется аутентификация

### Управление тикетами

#### POST /tech_support/ticket/<int:pk>/take/
**Функция:** Взять тикет в работу

**Метод:** `POST`

**Разрешения:** Требуется статус staff или superuser

#### POST /tech_support/ticket/<int:pk>/close/
**Функция:** Закрыть тикет

**Метод:** `POST`

**Разрешения:** Требуется статус staff или superuser

#### POST /tech_support/ticket/<int:pk>/comment/
**Функция:** Добавить комментарий к тикету

**Метод:** `POST`

**Разрешения:** Автор тикета или сотрудники поддержки

**Параметры запроса:**
```json
{
  "content": "Текст комментария"
}
```

#### POST /tech_support/ticket/<int:pk>/update/
**Функция:** Обновить параметры тикета

**Метод:** `POST`

**Разрешения:** Требуется статус staff или superuser

**Параметры запроса:**
```json
{
  "title": "Новый заголовок",
  "status": 1,
  "priority": 2,
  "category": 1,
  "deadline": "2024-12-31T23:59:59",
  "assigned_to": 5
}
```

### Отчеты и аналитика

#### GET /tech_support/reports/
**Функция:** Отчеты по тикетам

**Метод:** `GET`

**Разрешения:** Требуется статус staff или superuser

**Параметры запроса:**
- `period` - Период отчета (week/month/year)

#### GET /tech_support/dashboard/
**Функция:** Дашборд для сотрудников поддержки

**Метод:** `GET`

**Разрешения:** Требуется статус staff или superuser

## Представления (Views)

### TicketCreateView
**Функция:** `TicketCreateView`
**URL:** `/tech_support/chat/`
**Метод:** `POST`

**Функциональность:**
- Создание нового тикета
- Автоматическое назначение категории "Не распределено"
- Автоматическое назначение приоритета "Высокий"
- Обработка вложений
- Валидация данных

**Логика работы:**
1. Валидация формы
2. Создание тикета с автозаполнением полей
3. Обработка вложений
4. Редирект на страницу тикета

### TicketDetailView
**Функция:** `TicketDetailView`
**URL:** `/tech_support/ticket/<int:pk>/`
**Метод:** `GET`, `POST`

**Функциональность:**
- Детальный просмотр тикета
- Отображение комментариев и вложений
- Формы для обновления (для сотрудников)
- Оценка решения (для автора)

**Логика работы:**
1. Проверка прав доступа
2. Загрузка данных тикета
3. Обработка POST запросов (комментарии, обновления)
4. Отображение шаблона

### TicketListView
**Функция:** `TicketListView`
**URL:** `/tech_support/tickets/`
**Метод:** `GET`

**Функциональность:**
- Список всех тикетов для сотрудников
- Фильтрация и поиск
- Пагинация

### MyTicketListView
**Функция:** `MyTicketListView`
**URL:** `/tech_support/my-tickets/`
**Метод:** `GET`

**Функциональность:**
- Список тикетов пользователя
- Простой интерфейс без фильтров

### StaffDashboardView
**Функция:** `StaffDashboardView`
**URL:** `/tech_support/dashboard/`
**Метод:** `GET`

**Функциональность:**
- Статистика по тикетам
- Графики и метрики
- Быстрые действия

## Формы

### TicketCreateForm
**Функция:** Создание тикета

**Поля:**
- `title` - Заголовок (TextInput)
- `description` - Описание (Textarea)
- `attachments` - Вложение (FileInput)

**Валидация:**
- Заголовок: минимум 5 символов
- Описание: минимум 10 символов
- Файл: максимум 10MB, разрешенные форматы

### TicketCommentForm
**Функция:** Добавление комментария

**Поля:**
- `content` - Содержание (Textarea)

### TicketStaffUpdateForm
**Функция:** Обновление тикета сотрудниками

**Поля:**
- `title` - Заголовок
- `status` - Статус
- `priority` - Приоритет
- `category` - Категория
- `deadline` - Дедлайн
- `assigned_to` - Исполнитель

### TicketRatingForm
**Функция:** Оценка решения тикета

**Поля:**
- `rating` - Оценка (1-5)
- `student_feedback` - Отзыв

## URL маршруты

### Основные маршруты
- `/tech_support/chat/` - Создание тикета
- `/tech_support/ticket/<int:pk>/` - Детальный просмотр тикета
- `/tech_support/tickets/` - Список тикетов (админы)
- `/tech_support/my-tickets/` - Мои тикеты
- `/tech_support/dashboard/` - Дашборд сотрудников
- `/tech_support/reports/` - Отчеты

### Действия с тикетами
- `/tech_support/ticket/<int:pk>/take/` - Взять в работу
- `/tech_support/ticket/<int:pk>/close/` - Закрыть тикет
- `/tech_support/ticket/<int:pk>/comment/` - Добавить комментарий
- `/tech_support/ticket/<int:pk>/update/` - Обновить тикет

### Включение в основной проект
```python
# myproject/urls.py
path('tech_support/', include('apps.tech_support.urls'), name='tech_support'),
```

## Шаблоны

### support_chat.html
**Функция:** Форма создания тикета

**Особенности:**
- Упрощенный интерфейс (только заголовок и описание)
- Drag & drop для файлов
- JavaScript валидация
- Адаптивный дизайн

### ticket_detail.html
**Функция:** Детальный просмотр тикета

**Особенности:**
- Полная информация о тикете
- Комментарии с разметкой
- Вложения с возможностью скачивания
- Формы для сотрудников
- Система оценок

### ticket_list.html
**Функция:** Список тикетов для админов

**Особенности:**
- Таблица с фильтрацией
- Быстрые действия
- Статусы и приоритеты
- Поиск

### staff_dashboard.html
**Функция:** Дашборд сотрудников

**Особенности:**
- Статистика в реальном времени
- Графики и метрики
- Быстрые действия
- Уведомления

## Интеграция с другими приложениями

### Связь с пользователями
```python
# Автоматическое создание профиля при создании тикета
ticket.created_by = request.user
```

### Связь с курсами
```python
# Возможность привязки тикетов к курсам
ticket.course = course_instance
```

### Уведомления
```python
# Отправка уведомлений при изменении статуса
send_notification(ticket.assigned_to, f"Новый тикет: {ticket.title}")
```

## Безопасность

### Аутентификация и авторизация
- Все представления требуют аутентификации
- Специальные права для сотрудников поддержки
- Проверка доступа к тикетам

### Валидация данных
- Проверка размера файлов (максимум 10MB)
- Валидация типов файлов
- Санитизация HTML контента
- CSRF защита

### Права доступа
- Пользователи видят только свои тикеты
- Сотрудники видят все тикеты
- Внутренние комментарии только для сотрудников

## Производительность

### Оптимизация запросов
```python
# Использование select_related для связанных объектов
tickets = Ticket.objects.select_related('status', 'priority', 'category', 'created_by')
```

### Кэширование
```python
# Кэширование статистики дашборда
@cache_page(60 * 5)  # 5 минут
def staff_dashboard(request):
    # ...
```

### Пагинация
```python
# Пагинация списков тикетов
class TicketListView(ListView):
    paginate_by = 20
```

## Мониторинг и логирование

### Логирование действий
```python
import logging

logger = logging.getLogger(__name__)

def create_ticket(request):
    logger.info(f"New ticket created by {request.user}: {ticket.title}")
    # ...
```

### Метрики
- Количество созданных тикетов
- Время решения тикетов
- Оценки пользователей
- Загрузка сотрудников

## Тестирование

### Unit тесты
```python
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Ticket, TicketStatus, TicketPriority

class TicketModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.status = TicketStatus.objects.create(name='Открыт')
        self.priority = TicketPriority.objects.create(
            name='Высокий',
            level=1,
            response_time_hours=24
        )
    
    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Description',
            created_by=self.user,
            status=self.status,
            priority=self.priority
        )
        self.assertEqual(ticket.title, 'Test Ticket')
        self.assertTrue(ticket.ticket_number)
```

### Интеграционные тесты
```python
class TicketViewTest(TestCase):
    def test_ticket_creation_view(self):
        response = self.client.post('/tech_support/chat/', {
            'title': 'Test Ticket',
            'description': 'Test Description'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(title='Test Ticket').exists())
```

## Развертывание

### Требования
- Django 3.2+
- Pillow (для обработки изображений)
- PostgreSQL/MySQL
- Nginx/Apache для обслуживания файлов

### Настройки
```python
# settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Настройки для файлов
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

### Production рекомендации
- Использование CDN для файлов
- Настройка мониторинга
- Резервное копирование
- Rate limiting для API

## Расширение функциональности

### Добавление новых типов тикетов
```python
# В модели Ticket
TICKET_TYPES = [
    # ... существующие типы
    ('billing', 'Вопросы по оплате'),
    ('feature_request', 'Запрос функций'),
]
```

### Интеграция с внешними системами
```python
# Webhook для уведомлений
def send_webhook(ticket, action):
    requests.post(settings.WEBHOOK_URL, {
        'ticket_id': ticket.id,
        'action': action,
        'timestamp': timezone.now().isoformat()
    })
```

### Добавление тегов
```python
class TicketTag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)
    tickets = models.ManyToManyField(Ticket, related_name='tags')
```
