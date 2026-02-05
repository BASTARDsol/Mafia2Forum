import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_topicsubscription_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('topic', 'Topic update'), ('comment', 'Comment update'), ('mention', 'Mention'), ('like', 'Like')], max_length=20),
        ),
        migrations.CreateModel(
            name='Dialog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='DialogParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('dialog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dialog_participants', to='main.dialog')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dialog_participations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('dialog', 'user')},
            },
        ),
        migrations.AddField(
            model_name='dialog',
            name='participants',
            field=models.ManyToManyField(related_name='dialogs', through='main.DialogParticipant', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to=settings.AUTH_USER_MODEL)),
                ('dialog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='main.dialog')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
