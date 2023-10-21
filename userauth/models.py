from django.db import models


# Create your models here.
class TournamentPlayer(models.Model):
    discord_user_id = models.CharField(max_length=20, blank=True)
    discord_username = models.CharField(max_length=64)
    discord_global_name = models.CharField(max_length=64)
    discord_avatar = models.CharField(max_length=64)
    osu_user_id = models.BigIntegerField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['discord_user_id', 'osu_user_id'])
        ]
