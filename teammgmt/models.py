from django.db import models


# Create your models here.
class TournamentTeam(models.Model):
    osu_flag = models.CharField(max_length=4, primary_key=True)

    @classmethod
    def get_default_pk(cls):
        default_team, _ = cls.objects.get_or_create(
            osu_flag='WYSI',
        )
        return default_team.pk
