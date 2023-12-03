from django.contrib import admin
from userauth.models import TournamentPlayer
from teammgmt.models import TournamentTeam

# Register your models here.
admin.site.register(TournamentPlayer)
admin.site.register(TournamentTeam)
