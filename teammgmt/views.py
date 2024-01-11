from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from discord.views import TournamentPlayerSerializer, PreSharedKeyAuthentication, TeamOrganizer, ReadOnly
from teammgmt.models import TournamentTeam
from userauth.models import TournamentPlayer


class TournamentTeamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag']


class TournamentTeamMembersSerializer(serializers.HyperlinkedModelSerializer):
    candidates = serializers.SerializerMethodField()
    roster = serializers.SerializerMethodField()

    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag', 'roster', 'candidates']

    def get_candidates(self, team: TournamentTeam):
        qs = TournamentPlayer.objects.filter(team=team)
        pagination_class = viewsets.GenericViewSet.pagination_class
        all_candidates_serializer = TournamentPlayerSerializer(instance=qs,
                                                               context=self.context,
                                                               many=True,
                                                               read_only=True)

        if pagination_class is None or not issubclass(pagination_class, PageNumberPagination):
            return all_candidates_serializer.data

        request = self.context['request']
        drf_paginator = pagination_class()

        paginated_qs = drf_paginator.paginate_queryset(queryset=qs, request=request)

        # paginator was misconfigured
        if paginated_qs is None:
            return all_candidates_serializer.data

        paginated_response = drf_paginator.get_paginated_response(paginated_qs)

        # get_page_size cannot be None here else paginated_qs would've been None
        django_paginator = drf_paginator.django_paginator_class(qs, drf_paginator.get_page_size(request))
        page_num = drf_paginator.get_page_number(self.context['request'], django_paginator)

        page_results = django_paginator.page(page_num)
        paginated_response_data = paginated_response.data
        paginated_response_data['results'] = TournamentPlayerSerializer(instance=page_results,
                                                                        context=self.context,
                                                                        many=True,
                                                                        read_only=True).data
        return paginated_response_data

    def get_roster(self, team):
        players = TournamentPlayer.objects.filter(team=team, in_roster=True)
        serializer = TournamentPlayerSerializer(instance=players, context=self.context, many=True)
        return serializer.data


class TournamentTeamViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentTeamSerializer
    queryset = TournamentTeam.objects.all()
    http_method_names = ["get", "patch"]
    permission_classes = [ReadOnly]

    @action(methods=['get', 'PATCH'],
            detail=True,
            permission_classes=[PreSharedKeyAuthentication | TeamOrganizer | IsAdminUser])
    def members(self, request, **kwargs):
        """
        only organizer of team and admins can see team registrants and roster
        :param request:
        :param kwargs:
        :return:
        """
        team = self.get_object()
        if request.method == "PATCH" and 'players' in request.data:
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
