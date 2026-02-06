from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0009_familytask_assignee_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="familytask",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="familytask",
            name="completion_proof",
            field=models.ImageField(blank=True, null=True, upload_to="family/tasks/proofs/"),
        ),
    ]
