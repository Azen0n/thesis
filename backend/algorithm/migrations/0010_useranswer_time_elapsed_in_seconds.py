# Generated by Django 4.1.1 on 2023-05-21 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('algorithm', '0009_useranswer_coefficient_alter_progress_skill_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='useranswer',
            name='time_elapsed_in_seconds',
            field=models.FloatField(blank=True, null=True),
        ),
    ]