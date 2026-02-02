from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Profile

class Command(BaseCommand):
    help = 'Создаёт профили для всех пользователей, у которых их нет'

    def handle(self, *args, **kwargs):
        users_without_profile = User.objects.filter(profile__isnull=True)
        count = 0
        for user in users_without_profile:
            Profile.objects.create(user=user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Создано {count} профилей'))
