# Generated by Django 5.0.6 on 2024-10-13 14:34

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0024_userquiz_time_left'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserPoint',
            new_name='UserScore',
        ),
        migrations.RenameField(
            model_name='userquiz',
            old_name='is_points_added',
            new_name='is_completed',
        ),
        migrations.RenameField(
            model_name='userscore',
            old_name='total_points',
            new_name='total_score',
        ),
        migrations.AddField(
            model_name='userquiz',
            name='is_score_added',
            field=models.BooleanField(default=False),
        ),
    ]
