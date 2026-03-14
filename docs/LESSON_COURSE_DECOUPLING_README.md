# Убирание жесткой привязки уроков к курсам

## Описание изменений

Убрана жесткая привязка уроков к курсам через ForeignKey. Теперь уроки могут быть независимыми в базе знаний и использоваться в нескольких курсах одновременно.

## Исправленные ошибки

### Ошибка в builder.views.LessonCreateView
**Проблема:** При попытке создать урок через `/builder/add/` возникала ошибка "Unknown field(s) (course) specified for Lesson"

**Причина:** В `LessonCreateView` и `LessonUpdateView` все еще использовалось старое поле `course` вместо нового `courses`

**Решение:** 
- Обновлены поля в `LessonCreateView.fields` и `LessonUpdateView.fields`
- Добавлен `form.save_m2m()` для сохранения связей many-to-many
- Исправлена админка `UserLessonTrajectoryAdmin`

**Файлы:** `myproject/apps/builder/views.py`, `myproject/apps/courses/admin.py`

## Что изменено

### 1. Модель Lesson (myproject/apps/courses/models.py)

**Было:**
```python
course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='lessons', verbose_name="Курс")
```

**Стало:**
```python
# Связь many-to-many с курсами для гибкости
courses = models.ManyToManyField(
    Course,
    blank=True,
    related_name='course_lessons',
    verbose_name="Курсы, в которых используется урок"
)
```

### 2. Модель Course (myproject/apps/courses/models.py)

**Добавлено:**
```python
@property
def lessons(self):
    """Получение уроков курса через связь many-to-many"""
    return self.course_lessons.all().order_by('order')
```

### 3. Методы Lesson

**Обновлены методы получения предыдущего/следующего урока:**
- `get_previous_lesson(course=None)` - теперь принимает курс как параметр
- `get_next_lesson(course=None)` - теперь принимает курс как параметр

### 4. Формы (myproject/apps/courses/forms.py)

**LessonForm:**
- Добавлено поле `courses` для выбора курсов
- Обновлены labels и help_texts

**UserLessonTrajectoryForm:**
- Обновлена валидация для работы с новой структурой

### 5. Представления (myproject/apps/courses/views.py)

**Обновлены функции:**
- `lesson_detail()` - работает с новой структурой
- `create_lesson()` - создает урок с привязкой к курсам
- `add_lesson()` - добавляет уроки в курс через many-to-many
- `delete_lesson()` - удаляет связь с курсом, а не сам урок
- `edit_lesson()` - работает с новой структурой
- `complete_lesson()` - обновлена для новой структуры

### 6. Представления (myproject/apps/builder/views.py)

**Обновлены классы:**
- `LessonCreateView` - убрано поле `course`, добавлено поле `courses`
- `LessonUpdateView` - убрано поле `course`, добавлено поле `courses`
- Добавлен `form.save_m2m()` для сохранения связей many-to-many

### 7. Админка (myproject/apps/courses/admin.py)

**LessonAdmin:**
- Обновлен для отображения курсов через many-to-many
- Добавлен `filter_horizontal` для поля `courses`

**CourseAdmin:**
- Добавлен `LessonInline` для управления уроками курса

**UserLessonTrajectoryAdmin:**
- Обновлен для работы с новой структурой
- Убрано `lessons` из `autocomplete_fields`

### 8. Шаблоны

**lesson_detail.html:**
- Обновлен для работы с курсом из контекста
- Убраны ссылки на `lesson.course`

**notification_detail.html:**
- Обновлен для отображения всех курсов урока

### 9. Модель UserProgress (myproject/apps/myapp/models.py)

**Обновлен метод save:**
```python
def save(self, *args, **kwargs):
    if not self.course_id:
        # Получаем первый курс из связанных с уроком
        self.course = self.lesson.courses.first()
    super().save(*args, **kwargs)
```

## Миграции

### 0014_remove_lesson_lesson_course_order_idx_and_more.py
- Удаляет поле `course` из модели Lesson
- Удаляет индекс `lesson_course_order_idx`
- Добавляет поле `courses` (ManyToManyField)
- Создает индекс `lesson_order_idx`

### 0015_migrate_lesson_course_data.py
- Переносит данные из старого поля `course` в новое поле `courses`
- Обратная миграция очищает все связи

## Преимущества новой структуры

1. **Гибкость**: Уроки могут использоваться в нескольких курсах
2. **Независимость**: Уроки существуют независимо от курсов в базе знаний
3. **Переиспользование**: Один урок может быть частью разных образовательных программ
4. **Масштабируемость**: Легче добавлять новые курсы и переиспользовать существующие уроки

## Обратная совместимость

- Все существующие функции работают как прежде
- API остался совместимым благодаря property `lessons` в модели Course
- Шаблоны обновлены для работы с новой структурой

## Тестирование

После применения изменений рекомендуется:

1. Проверить создание новых уроков
2. Проверить добавление уроков в курсы
3. Проверить навигацию между уроками
4. Проверить работу траекторий
5. Проверить админку Django
