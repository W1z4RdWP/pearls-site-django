# Интеграция системы геймификации

## Что было добавлено

### 1. Модели данных
- **Profile.dascoin_points** - поле для хранения баллов DASCOIN
- **Badge** - модель для бейджей
- **Achievement** - модель для достижений  
- **UserBadge** - связь пользователей с бейджами
- **UserAchievement** - связь пользователей с достижениями

### 2. Интерфейс пользователя
- Секция DASCOIN с отображением текущего баланса
- Карточки бейджей и достижений в профиле
- Адаптивный дизайн для мобильных устройств
- Интерактивные элементы с анимацией

### 3. Система начисления баллов
- Автоматическое начисление баллов
- Автоматическая выдача бейджей при достижении порогов
- Утилиты для выдачи достижений

## Интеграция в существующие процессы

### Начисление баллов за курсы
Добавить в логику завершения курса:

```python
from gamification.utils import award_dascoin_points, award_course_badge

# При завершении курса
def complete_course(user, course):
    # Существующая логика...
    
    # Начисляем баллы
    award_dascoin_points(user, 150, f"Завершение курса {course.title}")
    
    # Выдаем бейдж за курс
    award_course_badge(user, course.title)
```

### Начисление баллов за тесты
Добавить в логику прохождения теста:

```python
from gamification.utils import award_dascoin_points, award_achievement

# При прохождении теста
def complete_quiz(user, quiz, score):
    # Существующая логика...
    
    # Базовые баллы за тест
    base_points = 50
    if score == 100:
        base_points = 100  # Бонус за идеальный результат
        award_achievement(user, "perfect_score", "Отличник", "Получил 100% за тест")
    
    award_dascoin_points(user, base_points, f"Прохождение теста {quiz.title}")
```

### Начисление баллов за уроки
Добавить в логику завершения урока:

```python
from gamification.utils import award_dascoin_points

# При завершении урока
def complete_lesson(user, lesson):
    # Существующая логика...
    
    # Начисляем баллы за урок
    award_dascoin_points(user, 10, f"Завершение урока {lesson.title}")
```

### Начисление баллов за траектории
Добавить в логику завершения траектории:

```python
from gamification.utils import award_dascoin_points, award_trajectory_badge

# При завершении траектории
def complete_trajectory(user, trajectory):
    # Существующая логика...
    
    # Начисляем баллы за траекторию
    award_dascoin_points(user, 500, f"Завершение траектории {trajectory.title}")
    
    # Выдаем бейдж за траекторию
    award_trajectory_badge(user, trajectory.title)
```

## Команды для управления

### Создание тестовых данных
```bash
python manage.py create_sample_badges
python manage.py create_default_icons
```

### Начисление тестовых баллов
```bash
python manage.py award_test_points username points
```

### Проверка статистики пользователя
```python
from gamification.utils import get_user_gamification_stats
from django.contrib.auth.models import User

user = User.objects.get(username='username')
stats = get_user_gamification_stats(user)
print(stats)
```

## Администрирование

### Доступ к админке
- Бейджи: `/admin/gamification/badge/`
- Достижения: `/admin/gamification/achievement/`
- Бейджи пользователей: `/admin/gamification/userbadge/`
- Достижения пользователей: `/admin/gamification/userachievement/`

### Создание новых бейджей
1. Перейти в админку бейджей
2. Создать новый бейдж
3. Указать тип, требуемые баллы, описание
4. Загрузить иконку (или использовать команду create_default_icons)

### Создание новых достижений
1. Перейти в админку достижений
2. Создать новое достижение
3. Указать тип, описание
4. Загрузить иконку

## Расширение функциональности

### Добавление новых типов бейджей
1. Добавить новый тип в `BADGE_TYPES` в модели Badge
2. Создать соответствующую функцию в utils.py
3. Интегрировать в нужные процессы

### Добавление новых типов достижений
1. Добавить новый тип в `ACHIEVEMENT_TYPES` в модели Achievement
2. Создать соответствующую функцию в utils.py
3. Интегрировать в нужные процессы

### Кастомизация дизайна
- CSS файл: `apps/users/static/users/css/profile.css`
- JavaScript: `apps/users/static/users/js/scripts.js`
- Шаблон: `apps/users/templates/users/profile.html`

## Мониторинг и аналитика

### Отслеживание активности
```python
from gamification.models import UserBadge, UserAchievement

# Статистика по бейджам
badge_stats = UserBadge.objects.values('badge__name').annotate(
    count=Count('id')
).order_by('-count')

# Статистика по достижениям
achievement_stats = UserAchievement.objects.values('achievement__name').annotate(
    count=Count('id')
).order_by('-count')
```

### Топ пользователей по баллам
```python
from users.models import Profile

top_users = Profile.objects.order_by('-dascoin_points')[:10]
```

## Безопасность

- Все операции с баллами выполняются в транзакциях
- Проверка уникальности бейджей и достижений
- Валидация данных на уровне моделей
- Логирование операций через Django Admin 