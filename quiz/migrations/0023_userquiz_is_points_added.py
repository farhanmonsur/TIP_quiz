# Generated by Django 5.0.6 on 2024-10-12 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0022_rename_userpoints_userpoint'),
    ]

    operations = [
        migrations.AddField(
            model_name='userquiz',
            name='is_points_added',
            field=models.BooleanField(default=False),
        ),
    ]
