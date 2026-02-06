from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_familytask_completion_proof"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="auto_close_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="topic",
            name="closed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="topic",
            name="is_closed",
            field=models.BooleanField(default=False),
        ),
    ]
