# Generated manually for data migration from course to courses

from django.db import migrations

def migrate_lesson_course_data(apps, schema_editor):
    """
    Переносим данные из старого поля course в новое поле courses (many-to-many)
    """
    Lesson = apps.get_model('courses', 'Lesson')
    Course = apps.get_model('courses', 'Course')
    
    # Получаем все уроки, которые были связаны с курсами
    for lesson in Lesson.objects.all():
        # Проверяем, есть ли у урока связанный курс через старую связь
        if hasattr(lesson, 'course') and lesson.course:
            # Добавляем курс в новое поле courses
            lesson.courses.add(lesson.course)

def reverse_migrate_lesson_course_data(apps, schema_editor):
    """
    Обратная миграция (если понадобится)
    """
    Lesson = apps.get_model('courses', 'Lesson')
    
    # Убираем все связи с курсами
    for lesson in Lesson.objects.all():
        lesson.courses.clear()

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_remove_lesson_lesson_course_order_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(
            migrate_lesson_course_data,
            reverse_migrate_lesson_course_data
        ),
    ]
