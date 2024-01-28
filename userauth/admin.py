from django.contrib import admin
from userauth.models import DisqualifiedUser, TournamentPlayer, TournamentPlayerBadge
from teammgmt.models import TournamentTeam

# Register your models here.
admin.site.register(TournamentPlayer)
admin.site.register(TournamentPlayerBadge)
admin.site.register(TournamentTeam)
admin.site.register(DisqualifiedUser)
