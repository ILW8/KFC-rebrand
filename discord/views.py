from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions, permissions, status
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from django.conf import settings
from rest_framework.response import Response

from userauth.models import TournamentPlayer
from rest_framework import serializers, viewsets


class PreSharedKeyAuthentication(TokenAuthentication, BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        auth = self.authenticate(request)
        return auth is not None

    def authenticate_credentials(self, key):
        if settings.DISCORD_PSK != key:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        return None, key


# Create your views here.
class TournamentPlayerSerializer(serializers.HyperlinkedModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = TournamentPlayer
        fields = ['user_id',
                  'discord_user_id',
                  'discord_username',
                  'osu_user_id',
                  'osu_username',
                  'osu_flag',
                  'is_organizer']


class TournamentPlayerViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentPlayerSerializer
    queryset = TournamentPlayer.objects.all()
    permission_classes = [PreSharedKeyAuthentication, ]

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
