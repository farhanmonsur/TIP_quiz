# Generated by Django 5.0.6 on 2024-10-14 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0028_userquiz_is_time_added_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userquiz',
            name='is_time_added_total',
        ),
        migrations.RemoveField(
            model_name='userquiz',
            name='play_time',
        ),
        migrations.RemoveField(
            model_name='userquiz',
            name='total_time',
        ),
    ]
