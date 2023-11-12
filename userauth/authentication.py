import json

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from userauth.models import TournamentPlayer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class DiscordAndOsuAuthBackend(BaseBackend):
    @staticmethod
    def validate_data(discord_user_data, osu_user_data):
        if discord_user_data is None or osu_user_data is None:
            return None, None

        discord_data = {'id': None, 'username': None, 'discriminator': None}
        for key in discord_data:
            discord_data[key] = discord_user_data.get(key)
        if None in discord_data.values():  # ensure all fields filled
            discord_data = None
        discord_data['composite_username'] = discord_data['username']
        discord_data['composite_username'] += f"#{discord_data['discriminator']}" \
            if discord_data['discriminator'] != '0' else ''

        osu_data = {'id': None, 'username': None, 'country_code': None}
        for key in osu_data:
            osu_data[key] = osu_user_data.get(key)
        if None in osu_data.values():
            osu_data = None
        return discord_data, osu_data

    # todo: split user creation from authentication
    def authenticate(self, request, discord_user_data=None, osu_user_data=None):
        discord_data, osu_data = self.validate_data(discord_user_data, osu_user_data)
        if discord_data is None or osu_data is None:
            return None

        username = f"{discord_data['id']}:{osu_data['id']}"
        try:
            # check both user and TournamentPlayer exist
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # found existing TournamentPlayer with different discord id
                tournament_player: TournamentPlayer = TournamentPlayer.objects.filter(osu_user_id=osu_data['id'])[0]
                tournament_player.discord_user_id = discord_data['id']
                tournament_player.discord_username = discord_data['composite_username']
                tournament_player.user.username = username
                tournament_player.user.save()
                tournament_player.save()
                return tournament_player.user
            except IndexError:
                pass

            # Create a new user. There's no need to set a password
            # because only the password from settings.py is checked.
            user = User(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.save()

        try:
            TournamentPlayer.objects.get(discord_user_id=discord_data['id'], osu_user_id=osu_data['id'])
        except TournamentPlayer.DoesNotExist:
            tourney_player = TournamentPlayer(user=user,
                                              discord_user_id=discord_data['id'],
                                              discord_username=discord_data['composite_username'],
                                              osu_user_id=osu_data['id'],
                                              osu_username=osu_data['username'],
                                              osu_flag=osu_data['country_code'])
            tourney_player.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(settings.CHANNELS_DISCORD_WS_GROUP_NAME,
                                                    {
                                                        "type": "registration.new",
                                                        "message": json.dumps({
                                                            "user_id": tourney_player.discord_user_id,
                                                            "is_organizer": tourney_player.is_organizer,
                                                            "action": "register"
                                                        })
                                                    })
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
