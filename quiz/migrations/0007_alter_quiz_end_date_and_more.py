# Generated by Django 5.0.6 on 2024-07-07 13:18

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0006_alter_quiz_end_date_alter_userquiz_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quiz',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.datetime(2024, 7, 7, 13, 18, 31, 214517, tzinfo=datetime.timezone.utc))]),
        ),
        migrations.AlterUniqueTogether(
            name='userquestionans',
            unique_together={('user_quiz', 'question', 'ans')},
        ),
    ]
