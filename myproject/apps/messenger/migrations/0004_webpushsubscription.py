import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0003_chatroomnotificationsettings'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WebPushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField(max_length=500, unique=True, verbose_name='Endpoint')),
                ('p256dh', models.CharField(max_length=255, verbose_name='Публичный ключ (p256dh)')),
                ('auth', models.CharField(max_length=255, verbose_name='Секрет (auth)')),
                ('user_agent', models.CharField(blank=True, max_length=500, verbose_name='User-Agent устройства')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='web_push_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Web Push подписка',
                'verbose_name_plural': 'Web Push подписки',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='webpushsubscription',
            index=models.Index(fields=['user'], name='messenger_w_user_id_idx'),
        ),
    ]
