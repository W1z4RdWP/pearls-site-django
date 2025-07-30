# Система геймификации

Система геймификации для платформы обучения включает в себя:

## Компоненты

### 1. Баллы DASCOIN
- Виртуальная валюта, которую получают сотрудники за выполнение заданий
- Начисляются за:
  - Просмотр уроков/курсов
  - Прохождение тестов
  - Завершение курсов и траекторий
  - Другие учебные активности

### 2. Бейджи
Виртуальные награды, которые выделяют участников обучения на фоне коллег. Получаются за:
- Набор определенного количества очков
- Завершение курса или траектории
- Освоение нового навыка
- Повышение категории

### 3. Достижения
Специальные награды в виде значков, которые можно получить за успехи в процессе обучения:
- Уникальны (присваиваются только одному сотруднику)
- Не могут быть закреплены за остальными
- Выдаются за особые достижения

## Модели

### Badge
- `name` - название бейджа
- `description` - описание
- `icon` - иконка бейджа
- `badge_type` - тип бейджа (points, course, trajectory, skill, category)
- `points_required` - требуемые баллы
- `is_active` - активен ли бейдж

### Achievement
- `name` - название достижения
- `description` - описание
- `icon` - иконка достижения
- `achievement_type` - тип достижения
- `is_unique` - уникальное ли достижение
- `is_active` - активно ли достижение

### UserBadge / UserAchievement
Связующие модели между пользователями и их наградами.

## Использование

### Начисление баллов
```python
from gamification.utils import award_dascoin_points

# Начислить 100 баллов пользователю
award_dascoin_points(user, 100, "За завершение курса")
```

### Выдача бейджей
```python
from gamification.utils import award_course_badge, award_trajectory_badge

# Бейдж за курс
award_course_badge(user, "Основы Python")

# Бейдж за траекторию
award_trajectory_badge(user, "Веб-разработка")
```

### Выдача достижений
```python
from gamification.utils import award_achievement

# Уникальное достижение
award_achievement(user, "first_course", "Первый шаг", "Завершил первый курс")
```

### Получение статистики
```python
from gamification.utils import get_user_gamification_stats

stats = get_user_gamification_stats(user)
print(f"Баллы: {stats['dascoin_points']}")
print(f"Бейджи: {stats['total_badges']}")
print(f"Достижения: {stats['total_achievements']}")
```

## Команды управления

### Создание тестовых данных
```bash
python manage.py create_sample_badges
```

### Начисление тестовых баллов
```bash
python manage.py award_test_points username 500
```

## Интеграция

Система интегрирована в профиль пользователя и отображает:
- Текущий баланс DASCOIN
- Последние полученные бейджи (до 3)
- Последние полученные достижения (до 3)
- Общее количество наград

## Администрирование

Все модели доступны в Django Admin:
- `/admin/gamification/badge/` - управление бейджами
- `/admin/gamification/achievement/` - управление достижениями
- `/admin/gamification/userbadge/` - бейджи пользователей
- `/admin/gamification/userachievement/` - достижения пользователей 