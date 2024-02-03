import datetime

from django.conf import settings
from django.db import transaction, IntegrityError

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from discord.views import TournamentPlayerSerializer, PreSharedKeyAuthentication, TeamOrganizer, ReadOnly
from userauth.authentication import IsSuperUser
from teammgmt.models import TournamentTeam
from userauth.models import TournamentPlayer


class TournamentTeamSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag']


class TournamentTeamMembersSerializer(serializers.HyperlinkedModelSerializer):
    candidates = serializers.SerializerMethodField()
    roster = serializers.SerializerMethodField()
    backups = serializers.SerializerMethodField()

    class Meta:
        model = TournamentTeam
        fields = ['url', 'osu_flag', 'roster', 'backups', 'candidates']

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

    def get_backups(self, team):
        players = TournamentPlayer.objects.filter(team=team, in_backup_roster=True)
        serializer = TournamentPlayerSerializer(instance=players, context=self.context, many=True)
        return serializer.data


class TournamentTeamViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentTeamSerializer
    queryset = TournamentTeam.objects.all()
    http_method_names = ["get", "patch"]
    permission_classes = [ReadOnly]

    @action(methods=['get', 'PATCH'],
            detail=True,
            permission_classes=[PreSharedKeyAuthentication | TeamOrganizer | IsSuperUser])
    def members(self, request, **kwargs):
        """
        only organizer of team and admins can see team registrants and roster
        :param request:
        :param kwargs:
        :return:
        """
        team = self.get_object()
        if request.method == "PATCH":
            request_time = datetime.datetime.now(tz=datetime.timezone.utc)
            if request_time < settings.TEAM_ROSTER_REGISTRATION_START:
                delta_seconds = (settings.TEAM_ROSTER_REGISTRATION_START - request_time)
                delta_seconds = delta_seconds - datetime.timedelta(microseconds=delta_seconds.microseconds)  # rm usec
                raise PermissionDenied(f"Registration opens in {delta_seconds} "
                                       f"({delta_seconds.total_seconds():.0f} seconds).")
            if request_time > settings.TEAM_ROSTER_SELECTION_END:
                time_delta = request_time - settings.TEAM_ROSTER_REGISTRATION_START
                time_delta = time_delta - datetime.timedelta(microseconds=time_delta.microseconds)
                raise PermissionDenied(f"Roster selection closed {time_delta} ago "
                                       f"({time_delta.total_seconds():.0f} seconds).")

            if not ((required_fields := {'players', 'backups'}) <= (keys_provided := request.data.keys())):
                return Response({"error": f"required field(s) "
                                          f"missing: {(keys_provided & required_fields) ^ required_fields}"},
                                status=status.HTTP_400_BAD_REQUEST)
            players = request.data['players']
            backups = request.data['backups']

            # check roster size
            # TODO: only allow reserve players if main roster meets minimum roster size
            if not all([len(players) <= settings.TEAM_ROSTER_SIZE_MAX,
                        len(backups) <= settings.TEAM_ROSTER_BACKUP_SIZE_MAX]):
                return Response(
                    {"error": f"roster and backup player count out of bounds; "
                              f"request roster size: {len(players)}, "
                              f"request backups size: {len(backups)}, "
                              f"minimum roster size: {settings.TEAM_ROSTER_SIZE_MIN}, "
                              f"maximum roster size: {settings.TEAM_ROSTER_SIZE_MAX}, "
                              f"maximum backup players: {settings.TEAM_ROSTER_BACKUP_SIZE_MAX}",
                     "roster_min": settings.TEAM_ROSTER_SIZE_MIN,
                     "roster_max": settings.TEAM_ROSTER_SIZE_MAX,
                     "backup_max": settings.TEAM_ROSTER_BACKUP_SIZE_MAX
                     },
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                req_players_qs = TournamentPlayer.objects.filter(pk__in=players)
            except TypeError:
                return Response({'error': 'players: expected array of player IDs'},
                                status=status.HTTP_400_BAD_REQUEST)
            original_players_qs = team.players.filter(in_roster=True)
            to_remove_from_roster = original_players_qs.exclude(pk__in=req_players_qs)

            try:
                req_backups_qs = TournamentPlayer.objects.filter(pk__in=backups)
            except TypeError:
                return Response({'error': 'backups: expected array of backup player IDs'},
                                status=status.HTTP_400_BAD_REQUEST)
            original_backups_qs = team.players.filter(in_backup_roster=True)
            to_remove_from_backup = original_backups_qs.exclude(pk__in=req_backups_qs)

            try:
                with transaction.atomic():
                    for player_to_remove_from_roster in to_remove_from_roster:
                        player_to_remove_from_roster.in_roster = False
                        player_to_remove_from_roster.save()
                    for player_to_remove_from_backup in to_remove_from_backup:
                        player_to_remove_from_backup.in_backup_roster = False
                        player_to_remove_from_backup.save()
                    req_players_qs.update(in_roster=True)
                    req_backups_qs.update(in_backup_roster=True)
            except IntegrityError as e:
                if str(e) == 'CHECK constraint failed: not_both_roster_and_backup':
                    return Response({"error": "player cannot be both in roster and "
                                              "backup roster at the same time"},
                                    status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": f"got unexpected exception: {repr(e)}"},
                                status=status.HTTP_400_BAD_REQUEST)
        serializer = TournamentTeamMembersSerializer(team, context={'request': request}, partial=True)
        return Response(serializer.data)
