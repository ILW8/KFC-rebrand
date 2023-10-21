from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from userauth.models import TournamentPlayer


class DiscordAndOsuAuthBackend(BaseBackend):
    def authenticate(self, request, discord_user_data=None, osu_user_data=None):
        if discord_user_data is None or osu_user_data is None:
            return None
        if (discord_user_id := discord_user_data.get("id")) is None or \
                (osu_user_id := osu_user_data.get("id")) is None:
            return None

        username = f"{discord_user_id}:{osu_user_id}"
        try:
            # check both user and tournamentplayer exist
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # check if tourneyplayer already exists with either discord or osu id
            tpqs = TournamentPlayer.objects.filter(discord_user_id=discord_user_id)
            if tpqs.count() > 0:
                # found existing tournamentplayer with different osu id
                tournament_player: TournamentPlayer = tpqs[0]
                tournament_player.osu_user_id = osu_user_id
                user = tournament_player.user
                user.username = username
                user.save()
                tournament_player.save()
                return user

            tpqs = TournamentPlayer.objects.filter(osu_user_id=osu_user_id)
            if tpqs.count() > 0:
                # found existing tournamentplayer with different discord id
                tournament_player: TournamentPlayer = tpqs[0]
                tournament_player.discord_user_id = discord_user_id
                user = tournament_player.user
                user.username = username
                user.save()
                tournament_player.save()
                return user

            # Create a new user. There's no need to set a password
            # because only the password from settings.py is checked.
            user = User(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.save()

        try:
            TournamentPlayer.objects.get(discord_user_id=discord_user_id, osu_user_id=osu_user_id)
        except TournamentPlayer.DoesNotExist:
            tourney_player = TournamentPlayer(user=user, discord_user_id=discord_user_id, osu_user_id=osu_user_id)
            tourney_player.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
