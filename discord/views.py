import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, permissions, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from userauth.authentication import filter_badges
from userauth.models import TournamentPlayer, TournamentPlayerBadge


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class PreSharedKeyAuthentication(TokenAuthentication, BasePermission):
    def has_permission(self, request, view):
        auth = self.authenticate(request)
        return auth is not None

    def authenticate_credentials(self, key):
        if settings.DISCORD_PSK != key:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        return None, key


class TeamOrganizer(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False
        if not request.user.tournamentplayer.is_organizer or request.user.tournamentplayer.team != obj:
            return False

        return True


class TournamentPlayerSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tournamentplayer-detail')
    team_id = serializers.ReadOnlyField()
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    rank_standard = serializers.Field(source='osu_rank_std')
    bws_rank = serializers.Field(source='osu_rank_std_bws')

    # user = serializers.HyperlinkedRelatedField(view_name='user-detail', queryset=User.objects.all())

    class Meta:
        model = TournamentPlayer
        fields = ['url',
                  'user_id',
                  'discord_user_id',
                  'discord_username',
                  'osu_user_id',
                  'osu_username',
                  'osu_flag',
                  'osu_stats_updated',
                  'rank_standard',
                  'bws_rank',
                  'is_organizer',
                  'in_roster',
                  'in_backup_roster',
                  'team_id',
                  'team']


class BadgeSerializer(serializers.HyperlinkedModelSerializer):
    awarded_at = serializers.CharField(source='award_date')

    class Meta:
        model = TournamentPlayerBadge
        fields = ['description',
                  'awarded_at',
                  'url',
                  'image_url',
                  'image_url_2x']


class TournamentPlayerSerializerWithBadges(TournamentPlayerSerializer):
    # tournamentplayerbadge_set is the default `related_name` for badge -> tourney player relationship
    badges = serializers.SerializerMethodField()

    # use this to add `filtered_badge_count`
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['filtered_badges_count'] = len(representation['badges'])
        return representation

    def get_badges(self, tournament_player: TournamentPlayer):
        serializer = BadgeSerializer(instance=TournamentPlayerBadge.objects.filter(user=tournament_player),
                                     many=True,
                                     read_only=True,
                                     source='tournamentplayerbadge_set')
        unfiltered_badges = serializer.data
        cutoff_date = self.context['request'].query_params.get('badge_cutoff_date', None)
        if cutoff_date is not None:
            try:
                cutoff_date = datetime.datetime.fromtimestamp(int(cutoff_date), tz=datetime.timezone.utc)
            except ValueError:
                raise ValueError("Invalid badge_cutoff_date provided, please provide a unix timestamp")
        return filter_badges(unfiltered_badges, [], cutoff_date=cutoff_date)

    class Meta(TournamentPlayerSerializer.Meta):
        fields = TournamentPlayerSerializer.Meta.fields + ['badges', ]


class TournamentPlayerViewSet(viewsets.ModelViewSet):
    queryset = TournamentPlayer.objects.all()
    permission_classes = [PreSharedKeyAuthentication | ReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TournamentPlayerSerializerWithBadges
        return TournamentPlayerSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        # Lookup with pk
        lookup_type = self.request.query_params.get("key", None)
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        try:
            if lookup_type is None or lookup_type in ('id', 'pk'):
                return super().get_object()
        except Http404 as pk404:
            if lookup_url_kwarg not in self.kwargs:  # I'm no longer sure what purpose this really serves...
                raise pk404

        error_404 = Http404("No %s matches the given query." % queryset.model._meta.object_name)

        if lookup_type in ("pk", "id") or lookup_type is None:
            raise error_404

        match [lookup_type]:
            case ["discord" | "osu"]:
                try:
                    obj = queryset.get(**{f"{lookup_type}_user_id": self.kwargs[lookup_url_kwarg]})
                except queryset.model.DoesNotExist:
                    raise error_404
            case _:
                raise ValueError(f"optional query parameter key not valid: '{lookup_type}'. "
                                 f'Must be one of {("pk", "id", "discord", "osu")}')

        self.check_object_permissions(self.request, obj)
        return obj

    def update(self, request, **kwargs):
        return self.partial_update(request, **kwargs)

    def partial_update(self, request, pk=None, **kwargs):
        tournament_player = self.get_object()

        new_is_organizer = request.data.get("is_organizer")
        if new_is_organizer is None:
            return Response({"error": "required field `is_organizer` missing"}, status=status.HTTP_400_BAD_REQUEST)

        if type(new_is_organizer) is not bool:
            return Response({"error": "field `is_organizer` must be boolean"}, status=status.HTTP_400_BAD_REQUEST)

        if tournament_player.is_organizer != new_is_organizer:
            tournament_player.is_organizer = new_is_organizer
            tournament_player.save()
        serializer = self.get_serializer(tournament_player, many=False)
        return Response(serializer.data)
