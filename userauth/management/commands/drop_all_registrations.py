from django.core.management.base import BaseCommand, CommandError
from userauth.models import TournamentPlayer
from django.contrib.auth.models import User

import string
import random


class Command(BaseCommand):
    help = "Deletes all registrations from database"

    def handle(self, *args, **options):
        confirmation_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        self.stdout.write(f"Please enter confirmation code {confirmation_code} to proceed: ", ending="")
        user_input = input()
        if user_input != confirmation_code:
            raise CommandError("Confirmation code did not match, please try again...")

        User.objects.filter(tournamentplayer__in=TournamentPlayer.objects.all()).delete()

        self.stdout.write(
            self.style.NOTICE(f"deleting all registrations")
        )
