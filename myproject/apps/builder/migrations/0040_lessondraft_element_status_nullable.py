# Allow null/blank for element status so no option is selected by default

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('builder', '0039_lessondraft_content_element_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lessondraft',
            name='content_element_status',
            field=models.CharField(
                blank=True,
                choices=[('actual', 'Готово (актуально сейчас)'), ('needs_work', 'Нужно доработать')],
                max_length=20,
                null=True,
                verbose_name='Текст (актуально/нужно доработать)'
            ),
        ),
        migrations.AlterField(
            model_name='lessondraft',
            name='links_element_status',
            field=models.CharField(
                blank=True,
                choices=[('actual', 'Готово (актуально сейчас)'), ('needs_work', 'Нужно доработать')],
                max_length=20,
                null=True,
                verbose_name='Ссылки (актуально/нужно доработать)'
            ),
        ),
        migrations.AlterField(
            model_name='lessondraft',
            name='video_element_status',
            field=models.CharField(
                blank=True,
                choices=[('actual', 'Готово (актуально сейчас)'), ('needs_work', 'Нужно доработать')],
                max_length=20,
                null=True,
                verbose_name='Видео (актуально/нужно доработать)'
            ),
        ),
    ]
