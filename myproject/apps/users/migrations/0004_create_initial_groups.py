from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    group_names = [
        "Собственник",
        "Исполнительный директор",
        "Финансовый директор",
        "HR и кураторы по обучению",
        "Руководители направлений",
        "Медицинский персонал",
        "Администраторы ОС и ОП",
        "Методолог",
        "IT-специалисты",
        "Менеджер проекта",
        "Наставники",
        "Пациенты",
        "Партнер",
    ]
    for name in group_names:
        Group.objects.get_or_create(name=name)

def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    group_names = [
        "Собственник",
        "Исполнительный директор",
        "Финансовый директор",
        "HR и кураторы по обучению",
        "Руководители направлений",
        "Медицинский персонал",
        "Администраторы ОС и ОП",
        "Методолог",
        "IT-специалисты",
        "Менеджер проекта",
        "Наставники",
        "Пациенты",
        "Партнер",
    ]
    Group.objects.filter(name__in=group_names).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # замените на вашу последнюю миграцию
        ('auth', '0012_alter_user_first_name_max_length'),  # убедитесь, что зависимость на auth есть
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
