from django.shortcuts import render
from userauth.models import TournamentPlayer
from rest_framework import serializers, viewsets


# Create your views here.
class TournamentPlayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TournamentPlayer
        fields = ['discord_user_id', 'osu_user_id', 'is_organizer']


class TournamentPlayerViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentPlayerSerializer
    queryset = TournamentPlayer.objects.all()
