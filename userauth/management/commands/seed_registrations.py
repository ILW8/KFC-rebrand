import json
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import pathlib
import time
from django.contrib.auth import authenticate

from userauth.views import login_signal


class Command(BaseCommand):
    help = "Seeds tournament players into database"

    def add_arguments(self, parser):
        parser.add_argument("count", default=100, type=int, nargs='?')
        parser.add_argument("--shuffle", action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE(f"seeding {options['count']} registrations")
        )
        start_time = time.perf_counter()

        file_dir = pathlib.Path(__file__).parent.resolve()
        filename = "_guild_data.json"

        try:
            with open(file_dir.joinpath(filename), "r") as infile:
                discord_data = json.load(infile)
                if options['shuffle']:
                    random.shuffle(discord_data)
        except FileNotFoundError:
            raise CommandError(f"Seeding data file '{filename}' not found, "
                               f"please place it in {file_dir}")

        filename = "_osu_data.json"
        try:
            with open(file_dir.joinpath(filename), "r") as infile:
                osu_data = json.load(infile)
                if options['shuffle']:
                    random.shuffle(osu_data)
        except FileNotFoundError:
            raise CommandError(f"Seeding data file '{filename}' not found, "
                               f"please place it in {file_dir}")

        for i in range(options['count']):
            # todo: manually create users instead of relying on `authenticate`?
            # todo: use [bulk_create](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-create)
            user: User = authenticate(None, **{"discord_user_data": discord_data[i], "osu_user_data": osu_data[i]})
            if user is None:
                raise CommandError(f"failed to register user with {discord_data[i]} and {osu_data[i]}")
            # noinspection PyUnresolvedReferences
            login_signal.send("login",
                              payload={"user_id": user.tournamentplayer.discord_user_id,
                                       "is_organizer": user.tournamentplayer.is_organizer,
                                       "action": "register"})
            self.stdout.write(
                self.style.SUCCESS(f"[{i+1}/{options['count']}] "
                                   f"Created user {discord_data[i]['id']}:{osu_data[i]['id']}")
            )
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {options['count']} registrations in {time.perf_counter() - start_time:.3f}s")
        )
