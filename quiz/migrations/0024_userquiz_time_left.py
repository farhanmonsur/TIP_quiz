# Generated by Django 5.0.6 on 2024-10-13 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0023_userquiz_is_points_added'),
    ]

    operations = [
        migrations.AddField(
            model_name='userquiz',
            name='time_left',
            field=models.IntegerField(default=0),
        ),
    ]
