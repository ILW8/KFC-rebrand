from django.conf import settings
from django.db import models


# Create your models here.
class TournamentPlayer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)

    discord_user_id = models.CharField(max_length=20, blank=True)
    discord_username = models.CharField(max_length=64)
    discord_global_name = models.CharField(max_length=64)
    discord_avatar = models.CharField(max_length=64)

    osu_user_id = models.BigIntegerField(blank=True)
    osu_username = models.CharField(max_length=64)
    osu_flag = models.CharField(max_length=4)

    is_organizer = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['discord_user_id', 'osu_user_id'])
        ]
