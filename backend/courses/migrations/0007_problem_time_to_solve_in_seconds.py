# Generated by Django 4.1.1 on 2023-03-02 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_topic_parent_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='time_to_solve_in_seconds',
            field=models.FloatField(default=60),
            preserve_default=False,
        ),
    ]
