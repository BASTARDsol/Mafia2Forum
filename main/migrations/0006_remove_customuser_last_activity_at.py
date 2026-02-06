from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_customuser_last_activity_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='last_activity_at',
        ),
    ]
