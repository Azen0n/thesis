# Generated by Django 4.1.1 on 2023-02-20 07:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_topic_created_at'),
        ('algorithm', '0005_remove_progress_weakest_link_state_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicGraphEdge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.FloatField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course')),
                ('topic1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_topicgraphedge_set1', to='courses.topic')),
                ('topic2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_topicgraphedge_set2', to='courses.topic')),
            ],
        ),
    ]
