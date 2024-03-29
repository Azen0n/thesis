# Generated by Django 4.1.1 on 2023-06-02 04:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('algorithm', '0011_alter_useranswer_is_solved'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='progress',
            options={'ordering': ['user__username', 'topic__created_at']},
        ),
        migrations.AlterModelOptions(
            name='useranswer',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='userweakestlinkstate',
            options={'ordering': ['user__username']},
        ),
        migrations.AlterModelOptions(
            name='weakestlinkproblem',
            options={'ordering': ['user__username', 'group_number']},
        ),
        migrations.AlterModelOptions(
            name='weakestlinktopic',
            options={'ordering': ['user__username', 'group_number']},
        ),
    ]
