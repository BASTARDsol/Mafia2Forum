from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_topic_forum_features"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="family_rank",
            field=models.CharField(
                choices=[
                    ("associate", "Associate"),
                    ("soldier", "Soldato"),
                    ("capo", "Caporegime"),
                    ("consigliere", "Consigliere"),
                    ("don", "Don"),
                ],
                default="associate",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="FactionDossier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_name", models.CharField(max_length=120)),
                (
                    "side",
                    models.CharField(
                        choices=[("ally", "Союзник"), ("neutral", "Нейтрал"), ("enemy", "Враг")],
                        default="neutral",
                        max_length=10,
                    ),
                ),
                (
                    "threat_level",
                    models.CharField(
                        choices=[
                            ("low", "Низкий"),
                            ("medium", "Средний"),
                            ("high", "Высокий"),
                            ("critical", "Критический"),
                        ],
                        default="low",
                        max_length=10,
                    ),
                ),
                ("notes", models.TextField()),
                ("evidence_link", models.URLField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_dossiers", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="FamilyOperation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("objective", models.TextField()),
                ("scheduled_for", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planning", "Планирование"),
                            ("active", "В процессе"),
                            ("completed", "Завершена"),
                            ("cancelled", "Отменена"),
                        ],
                        default="planning",
                        max_length=20,
                    ),
                ),
                ("result_report", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "coordinator",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coordinated_operations", to=settings.AUTH_USER_MODEL),
                ),
                ("participants", models.ManyToManyField(blank=True, related_name="family_operations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["scheduled_for", "-created_at"]},
        ),
        migrations.CreateModel(
            name="FamilyTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField()),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Открыта"), ("in_progress", "Выполняется"), ("done", "Выполнена")],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("reward_points", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assignee",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="family_tasks", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "created_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_family_tasks", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["status", "due_at", "-created_at"]},
        ),
    ]
