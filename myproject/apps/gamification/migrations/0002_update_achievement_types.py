# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='achievement_type',
            field=models.CharField(
                choices=[
                    ('monthly_leader', 'Лидер месяца'),
                    ('department_erudite', 'Эрудит отдела'),
                    ('yearly_mentor', 'Наставник года'),
                    ('initiator', 'Инициатор'),
                    ('first_course', 'Первый курс'),
                    ('perfect_score', 'Идеальный результат'),
                    ('speed_learner', 'Быстрый ученик'),
                    ('persistent', 'Настойчивый'),
                    ('innovator', 'Новатор'),
                    ('mentor', 'Ментор'),
                    ('custom', 'Особое достижение'),
                ],
                max_length=20,
                verbose_name='Тип достижения'
            ),
        ),
    ] 