# Generated by Django 4.1.1 on 2023-05-21 12:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_semestercode_unique_id_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
