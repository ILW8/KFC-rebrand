from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rest_framework import viewsets, serializers, status
import requests
import os
import urllib.parse
from django.conf import settings

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from auth.serializers import UserSerializer
from rest_framework.decorators import api_view, action
from .models import TournamentPlayer


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# todo: move to settings
# DISCORD_REDIRECT_BASE = "http%3A%2F%2F127.0.0.1%3A8000%2Fauth%2Fdiscord%2F"
DISCORD_REDIRECT_BASE = "http://127.0.0.1:8000/auth/discord/"
DISCORD_REDIRECT_URI = f"{DISCORD_REDIRECT_BASE}discord_code"


class DiscordAuth(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def prompt_login(self, request):
        uri = (f"https://discord.com/oauth2/authorize"
               f"?response_type=code"
               f"&client_id={settings.DISCORD_CLIENT_ID}"
               f"&scope=identify"
               f"&redirect_uri={urllib.parse.quote(DISCORD_REDIRECT_URI)}"
               f"&prompt=consent")
        return HttpResponseRedirect(redirect_to=uri)

    @action(methods=['get'], detail=False)
    def discord_code(self, request):
        code = request.query_params.get("code", None)
        if code is None:
            return Response({"error": "missing `code` query param"}, status=status.HTTP_400_BAD_REQUEST)

        # return Response({"code": code})

        # access token exchange
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(f'{settings.DISCORD_API_ENDPOINT}/oauth2/token',
                          data=data,
                          headers=headers,
                          auth=(settings.DISCORD_CLIENT_ID, settings.DISCORD_CLIENT_SECRET))
        if r.status_code != 200:
            return Response(r.json(), status=r.status_code)

        auth_data = r.json()

        # fetch user information
        r = requests.get(f"{settings.DISCORD_API_ENDPOINT}/oauth2/@me",
                         headers={"Authorization": f"Bearer {auth_data.get('access_token')}"})
        if r.status_code != 200:
            return Response(r.json(), status=r.status_code)
        user_data = r.json().get("user")

        return Response(user_data, status=r.status_code)

        # check if user exists
        # if TournamentPlayer.objects.filter(discord_user_id)

    @action(methods=['get'], detail=False)
    def token(self, request):
        print(request.query_params.get("access_token"))
        return Response(request.query_params)

    def list(self, request):
        return Response({})

    def get_permissions(self):
        # """
        # Instantiates and returns the list of permissions that this view requires.
        # """
        # if self.action == 'list':
        #     permission_classes = [IsAuthenticated]
        # else:
        #     permission_classes = [IsAdminUser]
        return [AllowAny()]
