from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User


class DiscordAndOsuAuthBackend(BaseBackend):
    def authenticate(self, request, discord_user_data=None, osu_user_data=None):
        if discord_user_data is None or osu_user_data is None:
            return None
        if (discord_user_id := discord_user_data.get("id")) is None or \
                (osu_user_id := osu_user_data.get("__PLACEHOLDER__")) is None:
            return None

        if True:  # todo: add condition here
            username = f"{discord_user_id}:{osu_user_id}"
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. There's no need to set a password
                # because only the password from settings.py is checked.
                user = User(username=username)
                user.is_staff = False
                user.is_superuser = False
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
