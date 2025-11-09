from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('builder', '0020_remove_incident_responsible_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='violators',
            field=models.ManyToManyField(
                blank=True,
                related_name='violator_incidents',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Нарушители'
            ),
        ),
    ]
