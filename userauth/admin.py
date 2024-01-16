from django.contrib import admin
from userauth.models import TournamentPlayer, TournamentPlayerBadge
from teammgmt.models import TournamentTeam

# Register your models here.
admin.site.register(TournamentPlayer)
admin.site.register(TournamentPlayerBadge)
admin.site.register(TournamentTeam)
