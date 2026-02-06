from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_profile2_realtime_chat_activity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('goal', models.TextField()),
                ('scheduled_for', models.DateTimeField()),
                ('status', models.CharField(choices=[('planned', 'Запланирована'), ('active', 'В процессе'), ('done', 'Завершена')], default='planned', max_length=20)),
                ('result', models.TextField(blank=True)),
                ('lessons_learned', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('coordinator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='coordinated_operations', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(blank=True, related_name='operations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-scheduled_for'],
            },
        ),
        migrations.CreateModel(
            name='RecruitmentApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(max_length=150)),
                ('background', models.TextField()),
                ('status', models.CharField(choices=[('new', 'Новая'), ('check', 'Проверка'), ('trial', 'Испытательный срок'), ('approved', 'Принят'), ('rejected', 'Отклонён')], default='new', max_length=20)),
                ('decision_comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('curator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='curated_candidates', to=settings.AUTH_USER_MODEL)),
                ('recruiter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recruitment_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OperationChecklistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('is_done', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_checklist_items', to=settings.AUTH_USER_MODEL)),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist_items', to='main.operation')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
