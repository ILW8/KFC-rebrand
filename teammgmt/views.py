from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from discord.views import TournamentPlayerSerializer, PreSharedKeyAuthentication
from teammgmt.models import TournamentTeam
from userauth.models import TournamentPlayer


class TournamentTeamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag']


class TournamentTeamMembersSerializer(serializers.HyperlinkedModelSerializer):
    candidates = TournamentPlayerSerializer(many=True, read_only=True, source="players")
    roster = serializers.SerializerMethodField()

    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag', 'roster', 'candidates']

    def get_roster(self, team):
        players = TournamentPlayer.objects.filter(team=team, in_roster=True)
        serializer = TournamentPlayerSerializer(instance=players, context=self.context, many=True)
        return serializer.data


class TournamentTeamViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentTeamSerializer
    queryset = TournamentTeam.objects.all()
    http_method_names = ["get", "patch"]
    permission_classes = [PreSharedKeyAuthentication, ]

    @action(methods=['get', 'PATCH'], detail=True)
    def members(self, request, **kwargs):
        team = self.get_object()
        if request.method == "PATCH" and 'players' in request.data:
            if not request.user.tournamentplayer.is_organizer or request.user.tournamentplayer.team != team:
                return Response({'error': f'user is not team organizer for team {team.osu_flag}'},
                                status=status.HTTP_403_FORBIDDEN)
            players = request.data['players']
            try:
                req_players_qs = TournamentPlayer.objects.filter(pk__in=players)

            except TypeError:
                return Response({'error': 'expected array of player IDs'}, status=status.HTTP_400_BAD_REQUEST)

            original_players_qs = team.players.filter(in_roster=True)
            original_players_qs.exclude(pk__in=req_players_qs).update(in_roster=False)

            req_players_qs.update(in_roster=True)

        serializer = TournamentTeamMembersSerializer(team, context={'request': request}, partial=True)
        return Response(serializer.data)
