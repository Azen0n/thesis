# Generated by Django 4.1.1 on 2022-12-10 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_alter_problem_difficulty_alter_problem_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='type',
            field=models.CharField(choices=[('Multiple Choice Radio', 'Выбор одного варианта'), ('Multiple Choice Checkbox', 'Выбор нескольких вариантов'), ('Fill In Single Blank', 'Заполнение пропуска')], max_length=100),
        ),
    ]
