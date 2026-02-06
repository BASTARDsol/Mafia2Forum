from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_remove_customuser_last_activity_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, unique=True)),
                ('slug', models.SlugField(max_length=50, unique=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='topic',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topic',
            name='prefix',
            field=models.CharField(
                choices=[('discussion', 'Обсуждение'), ('question', 'Вопрос'), ('guide', 'Гайд'), ('important', 'Важно')],
                default='discussion',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='topic',
            name='status',
            field=models.CharField(
                choices=[('open', 'Открыта'), ('solved', 'Решено')],
                default='open',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='topic',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='topics', to='main.tag'),
        ),
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ['-is_pinned', '-created_at']},
        ),
    ]
