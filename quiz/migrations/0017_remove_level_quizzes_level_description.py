# Generated by Django 5.1.1 on 2024-10-02 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0016_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='level',
            name='quizzes',
        ),
        migrations.AddField(
            model_name='level',
            name='description',
            field=models.TextField(default=2),
            preserve_default=False,
        ),
    ]
