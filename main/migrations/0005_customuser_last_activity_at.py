from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_profile2_realtime_chat_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='last_activity_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
