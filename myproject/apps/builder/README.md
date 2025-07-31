# Приложение Builder - Система управления базой знаний

## Обзор

Приложение `builder` представляет собой комплексную систему управления базой знаний (БЗ), которая обеспечивает создание, редактирование, организацию и управление образовательным контентом. Это центральный модуль для администраторов и контент-менеджеров платформы.

## Архитектура

### Структура приложения

```
builder/
├── models.py                    # Модели данных
├── views.py                     # Логика представлений (1945 строк)
├── forms.py                     # Формы для работы с данными
├── urls.py                      # URL маршруты
├── admin.py                     # Административная панель
├── apps.py                      # Конфигурация приложения
├── tests.py                     # Тесты
├── tests_custom/                # Дополнительные тесты
├── templatetags/                # Пользовательские теги шаблонов
├── migrations/                  # Миграции базы данных
├── templates/builder/           # Шаблоны
│   ├── includes/                # Включаемые шаблоны
│   │   ├── _category_tree.html  # Дерево категорий
│   │   ├── _lesson_detail_block.html # Блок деталей урока
│   │   └── _dictionary_section_detail.html # Детали словаря
│   ├── master_detail.html       # Главная страница БЗ
│   ├── dashboard.html           # Панель управления
│   ├── lesson_form.html         # Форма урока
│   ├── category_form.html       # Форма категории
│   ├── trajectory_management.html # Управление траекториями
│   ├── trajectory_courses.html  # Курсы в траектории
│   ├── course_list.html         # Список курсов
│   ├── documents.html           # Управление документами
│   ├── incidents.html           # Управление инцидентами
│   └── ...                      # Другие шаблоны
└── static/builder/              # Статические файлы
    ├── css/                     # Стили
    │   ├── builder_style.css    # Основные стили
    │   ├── trajectory_managment.css # Стили управления траекториями
    │   ├── dict_table_style.css # Стили словаря
    │   ├── incidents.css        # Стили инцидентов
    │   └── update_control_form.css # Стили контроля обновлений
    └── js/                      # JavaScript
        ├── builder.js           # Основная логика (1931 строка)
        ├── trajectory_managment.js # Управление траекториями (819 строк)
        ├── dictTable.js         # Логика словаря (210 строк)
        ├── search.js            # Поиск (79 строк)
        └── ckeditor_target_blank.js # Настройки CKEditor
```

## Модели данных

### CategoryName (Категория)
Основная модель для организации контента в иерархическую структуру.

**Поля:**
- `name` - Название категории (CharField, max_length=200)
- `parent` - Родительская категория (ForeignKey на self, null=True, blank=True)
- `order` - Порядок сортировки (PositiveIntegerField, default=0)
- `allowed_groups` - Группы с доступом (ManyToManyField на Group)

**Особенности:**
- Поддержка неограниченной вложенности
- Автоматическое построение полного пути
- Контроль доступа на уровне групп
- Индексы для оптимизации запросов

**Методы:**
- `__str__()` - Возвращает полный путь категории

### Document (Документ)
Модель для хранения файлов в базе знаний.

**Поля:**
- `title` - Название документа (CharField, max_length=255)
- `file` - Файл (FileField, upload_to='documents/')
- `uploaded_at` - Дата загрузки (DateTimeField, auto_now_add=True)

### Incident (Инцидент)
Модель для отслеживания проблем и инцидентов в обучении.

**Поля:**
- `title` - Название инцидента (CharField, max_length=255)
- `user` - Сотрудник (ForeignKey на User)
- `incident_type` - Тип инцидента (CharField, choices)
- `description` - Описание (TextField)
- `related_documents` - Связанные документы (ManyToManyField на Document)
- `role` - Роль (CharField, max_length=128)
- `error_type` - Тип ошибки (CharField, max_length=128)
- `topic` - Тема (CharField, max_length=128)
- `status` - Статус (CharField, choices, default='new')
- `created_at` - Дата создания (DateTimeField, auto_now_add=True)
- `updated_at` - Дата обновления (DateTimeField, auto_now=True)

**Типы инцидентов:**
- `test_fail` - Провал теста
- `incident` - Инцидент
- `regulation_change` - Изменение регламента

**Статусы:**
- `new` - Новый
- `in_progress` - В работе
- `resolved` - Решён

### LessonVersion (Версия урока)
Модель для хранения истории изменений уроков.

**Поля:**
- `lesson` - Урок (ForeignKey на courses.Lesson)
- `version` - Номер версии (PositiveIntegerField)
- `title` - Название урока (CharField, max_length=200)
- `content` - Содержимое (TextField)
- `video_id` - ID видео (CharField, max_length=100)
- `updated_at` - Дата изменения (DateTimeField, auto_now_add=True)
- `updated_by` - Кто изменил (ForeignKey на User)
- `comment` - Комментарий (CharField, max_length=255)
- `next_update` - Дата следующего обновления (DateField)
- `update_period_days` - Период обновлений (IntegerField, default=90)

**Особенности:**
- Автоматическое версионирование
- Отслеживание автора изменений
- Планирование обновлений

### LessonCategoryMirror (Зеркало урока)
Модель для размещения одного урока в нескольких категориях.

**Поля:**
- `lesson` - Зеркалируемый урок (ForeignKey на courses.Lesson)
- `category` - Категория зеркала (ForeignKey на CategoryName)
- `order` - Порядок в категории (PositiveIntegerField, default=0)

**Особенности:**
- Аналог симлинка для уроков
- Каскадное удаление при удалении урока
- Сохранение связи при удалении категории

### DictionarySection (Отдел словаря)
Модель для организации терминов словаря по отделам.

**Поля:**
- `name` - Название отдела (CharField, max_length=200)
- `order` - Порядок (PositiveIntegerField, default=0)

### DictionaryTerm (Термин словаря)
Модель для хранения терминов и их определений.

**Поля:**
- `section` - Отдел (ForeignKey на DictionarySection)
- `term` - Термин (CharField, max_length=200)
- `slang` - Сленг (CharField, max_length=200)
- `definition` - Определение (TextField)
- `photo` - Фото (ImageField, upload_to='dict_photos/')
- `order` - Порядок (PositiveIntegerField, default=0)
- `created_at` - Дата создания (DateTimeField, auto_now_add=True)
- `updated_at` - Дата обновления (DateTimeField, auto_now=True)
- `author` - Автор (ForeignKey на User)

## Представления (Views)

### Основные представления

#### LessonMasterDetailView
**Класс:** `TemplateView`
**URL:** `/content/`
**Функция:** Главная страница базы знаний

**Особенности:**
- Отображение дерева категорий и уроков
- Поддержка поиска и фильтрации
- Контроль доступа на основе групп
- AJAX-обновления для динамического интерфейса

#### DashboardView
**Класс:** `TemplateView`
**URL:** `/`
**Функция:** Панель управления для администраторов

**Доступ:** Только staff/superuser

### Управление уроками

#### LessonCreateView
**Класс:** `CreateView`
**URL:** `/add/`, `/add/<int:category_id>/`
**Функция:** Создание нового урока

**Поля:** title, content, video_id, course, category
**Особенности:**
- Поддержка создания с предустановленной категорией
- Автоматическое создание версии
- Валидация Rutube URL

#### LessonUpdateView
**Класс:** `UpdateView`
**URL:** `/lesson/<int:pk>/edit/`
**Функция:** Редактирование урока

**Особенности:**
- Создание новой версии при изменении
- Сохранение истории изменений
- Обновление даты следующей актуализации

#### LessonDeleteView
**Класс:** `DeleteView`
**URL:** `/lesson/<int:pk>/delete/`
**Функция:** Удаление урока

### Управление категориями

#### CategoryListView
**Класс:** `ListView`
**URL:** `/categories/`
**Функция:** Список всех категорий

#### CategoryCreateView
**Класс:** `CreateView`
**URL:** `/categories/add/`
**Функция:** Создание категории

#### CategoryUpdateView
**Класс:** `UpdateView`
**URL:** `/categories/<int:pk>/edit/`
**Функция:** Редактирование категории

#### CategoryDeleteView
**Класс:** `DeleteView`
**URL:** `/categories/<int:pk>/delete/`
**Функция:** Удаление категории

### AJAX представления

#### ajax_add_root_category
**Функция:** `ajax_add_root_category(request)`
**URL:** `/categories/ajax_add_root/`
**Функция:** AJAX создание корневой категории

#### ajax_add_subcategory
**Функция:** `ajax_add_subcategory(request)`
**URL:** `/categories/ajax_add_sub/`
**Функция:** AJAX создание подкатегории

#### ajax_rename_category
**Функция:** `ajax_rename_category(request)`
**URL:** `/categories/ajax_rename/`
**Функция:** AJAX переименование категории

#### ajax_search_tree
**Функция:** `ajax_search_tree(request)`
**URL:** `/search/`
**Функция:** Поиск по дереву категорий и уроков

#### ajax_reorder
**Функция:** `ajax_reorder(request)`
**URL:** `/reorder/`
**Функция:** Изменение порядка элементов

### Операции с контентом

#### ajax_copy
**Функция:** `ajax_copy(request)`
**URL:** `/copy/`
**Функция:** Копирование уроков/категорий

#### ajax_cut
**Функция:** `ajax_cut(request)`
**URL:** `/cut/`
**Функция:** Вырезание уроков/категорий

#### ajax_paste
**Функция:** `ajax_paste(request)`
**URL:** `/paste/`
**Функция:** Вставка скопированных элементов

#### ajax_mirror
**Функция:** `ajax_mirror(request)`
**URL:** `/mirror/`
**Функция:** Создание зеркала урока

### Управление траекториями

#### TrajectoryManagementView
**Класс:** `TemplateView`
**URL:** `/trajectory-management/`
**Функция:** Централизованная панель управления траекториями

#### TrajectoryListView
**Класс:** `ListView`
**URL:** `/trajectories/`
**Функция:** Список траекторий

#### TrajectoryEditView
**Класс:** `UpdateView`
**URL:** `/trajectories/<int:pk>/edit/`
**Функция:** Редактирование траектории

#### TrajectoryCoursesView
**Класс:** `TemplateView`
**URL:** `/trajectories/<int:trajectory_id>/courses/`
**Функция:** Управление курсами в траектории

### Управление документами и инцидентами

#### DocumentListView
**Класс:** `ListView, FormView`
**URL:** `/documents/`
**Функция:** Просмотр и загрузка документов

#### IncidentListView
**Класс:** `ListView`
**URL:** `/incidents/`
**Функция:** Список инцидентов

#### IncidentCreateView
**Класс:** `CreateView`
**URL:** `/incidents/add/`
**Функция:** Создание инцидента

### Контроль обновлений

#### UpdateControlStandaloneView
**Класс:** `TemplateView`
**URL:** `/update_control/`
**Функция:** Централизованный мониторинг актуальности уроков

**Функциональность:**
- Отображение уроков, требующих обновления
- Планирование дат обновлений
- Отслеживание версий

## Формы (Forms)

### DocumentForm
Форма для загрузки документов в базу знаний.

**Поля:** title, file

### IncidentForm
Форма для создания/редактирования инцидентов.

**Поля:** title, user, incident_type, description, related_documents, role, error_type, topic, status
**Виджеты:** Textarea для описания, SelectMultiple для документов

## URL маршруты

### Основные маршруты
- `/` - Панель управления (редирект для неавторизованных)
- `/content/` - Главная страница БЗ
- `/dashboard/` - Панель управления

### Управление уроками
- `/lesson/<int:pk>/` - Детальная страница урока
- `/lesson/<int:pk>/edit/` - Редактирование урока
- `/lesson/<int:pk>/delete/` - Удаление урока
- `/add/` - Создание урока
- `/add/<int:category_id>/` - Создание урока в категории

### Управление категориями
- `/categories/` - Список категорий
- `/categories/add/` - Создание категории
- `/categories/<int:pk>/edit/` - Редактирование категории
- `/categories/<int:pk>/delete/` - Удаление категории

### AJAX операции
- `/categories/ajax_add_root/` - AJAX создание корневой категории
- `/categories/ajax_add_sub/` - AJAX создание подкатегории
- `/categories/ajax_rename/` - AJAX переименование
- `/search/` - Поиск по дереву
- `/reorder/` - Изменение порядка
- `/copy/`, `/cut/`, `/paste/` - Операции с контентом
- `/mirror/` - Создание зеркала

### Управление траекториями
- `/trajectory-management/` - Панель управления траекториями
- `/trajectories/` - Список траекторий
- `/trajectories/<int:pk>/edit/` - Редактирование траектории
- `/trajectories/<int:trajectory_id>/courses/` - Курсы в траектории

### Документы и инциденты
- `/documents/` - Управление документами
- `/incidents/` - Список инцидентов
- `/incidents/add/` - Создание инцидента

### Специальные функции
- `/update_control/` - Контроль обновлений
- `/actualize_version/` - Актуализация версий
- `/dictionary/<int:pk>/` - Детали словаря

## JavaScript функциональность

### builder.js (1931 строка)
Основной JavaScript файл для интерактивности БЗ.

**Основные функции:**
- Управление деревом категорий
- Drag & Drop операции
- AJAX запросы
- Поиск и фильтрация
- Операции копирования/вставки
- Создание зеркал

### trajectory_managment.js (819 строк)
Управление траекториями обучения.

**Функциональность:**
- Создание и редактирование траекторий
- Управление курсами в траекториях
- Drag & Drop для курсов
- Массовые операции

### dictTable.js (210 строк)
Управление словарем терминов.

**Возможности:**
- Редактирование терминов
- Сортировка и фильтрация
- Загрузка изображений

### search.js (79 строк)
Поисковая функциональность.

**Особенности:**
- Поиск в реальном времени
- Подсветка результатов
- Фильтрация по типам

## CSS стили

### builder_style.css (932 строки)
Основные стили для интерфейса БЗ.

**Компоненты:**
- Дерево категорий
- Формы уроков
- Модальные окна
- Drag & Drop элементы

### trajectory_managment.css (1321 строка)
Стили для управления траекториями.

**Особенности:**
- Сложные макеты
- Анимации
- Адаптивный дизайн

### dict_table_style.css (270 строк)
Стили для таблицы словаря.

### incidents.css (171 строка)
Стили для управления инцидентами.

### update_control_form.css (94 строки)
Стили для контроля обновлений.

## Вспомогательные функции

### get_category_tree_data(category_id)
Получение полного дерева категории со всеми подкатегориями, уроками и зеркалами.

### copy_category_tree(category_data, target_parent_id=None)
Копирование дерева категорий.

### move_category_tree(category_id, target_parent_id=None)
Перемещение дерева категорий.

### user_has_category_access(user, category)
Проверка доступа пользователя к категории.

### filter_categories_and_lessons_for_user(user, categories, uncategorized_lessons)
Фильтрация контента по правам доступа пользователя.

## Безопасность

### Аутентификация и авторизация
- Все административные функции требуют аутентификации
- Проверка прав staff/superuser для критических операций
- Контроль доступа на уровне групп пользователей

### CSRF защита
- Большинство AJAX функций используют `@csrf_exempt` (требует доработки)
- Формы защищены CSRF токенами

### Валидация данных
- Проверка прав доступа перед операциями
- Валидация входных данных в AJAX запросах
- Проверка существования объектов

## Производительность

### Оптимизация запросов
- Использование `select_related` и `prefetch_related`
- Индексы в базе данных
- Кэширование дерева категорий

### Frontend оптимизация
- Ленивая загрузка контента
- Debouncing для поиска
- Оптимизация DOM-операций

## Тестирование

### Структура тестов
- Unit тесты для моделей
- Интеграционные тесты для views
- Тесты AJAX функций

### tests_custom/
Дополнительные тесты для специфичной функциональности.

## Расширение функциональности

### Добавление новых типов контента
1. Создать модель в `models.py`
2. Добавить представления в `views.py`
3. Создать формы в `forms.py`
4. Добавить шаблоны
5. Обновить JavaScript

### Интеграция с внешними сервисами
- Поддержка других видеохостингов
- Интеграция с системами аналитики
- Экспорт данных

### Мобильная адаптация
- Адаптивные шаблоны
- Touch-события
- Оптимизация для мобильных устройств

## Отладка и мониторинг

### Логирование
- Логирование AJAX операций
- Отслеживание изменений контента
- Мониторинг производительности

### Инструменты отладки
- Django Debug Toolbar
- Логирование SQL запросов
- Профилирование JavaScript

## Развертывание

### Требования
- Django 3.2+
- PostgreSQL/MySQL
- Redis (для кэширования)
- Nginx/Apache

### Настройки
- Настройка медиа-файлов
- Конфигурация CKEditor
- Настройка кэширования

### Миграции
- Создание миграций: `python manage.py makemigrations builder`
- Применение миграций: `python manage.py migrate`

## Поддержка и документация

### Дополнительные ресурсы
- Документация Django
- Документация CKEditor
- Руководства по развертыванию

### Контакты
- Вопросы по разработке: [Владислав Кузнецов](https://t.me/w1z4rdWP)
