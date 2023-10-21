from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rest_framework import viewsets, serializers, status
import requests
import urllib.parse
from django.conf import settings

from rest_framework.response import Response

from rest_framework.decorators import action
from django.contrib.auth import authenticate, login, logout

from .models import TournamentPlayer

# todo: move to settings
# DISCORD_REDIRECT_BASE = "http%3A%2F%2F127.0.0.1%3A8000%2Fauth%2Fdiscord%2F"
DISCORD_REDIRECT_BASE = "http://127.0.0.1:8000/auth/discord/"
DISCORD_REDIRECT_URI = f"{DISCORD_REDIRECT_BASE}discord_code"
OSU_REDIRECT_URI = "http://127.0.0.1:8000/auth/osu/code"


class SessionDetails(viewsets.ViewSet):
    def list(self, request):
        return Response({
            "logged_in_user": request.user.username,
            "discord": request.session.get("discord_user_data"),
            "osu": request.session.get("osu_user_data")})

    @action(methods=['get', 'post'], detail=False)
    def logout(self, request):
        if request.session.get("discord_user_data") is not None:
            del request.session["discord_user_data"]
        if request.session.get("osu_user_data") is not None:
            del request.session["osu_user_data"]
        logout(request)
        return Response({"ok": "logged out"}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get', 'post'], detail=False)
    def login(self, request):
        user: User = authenticate(request,
                                  discord_user_data=request.session.get("discord_user_data"),
                                  osu_user_data=request.session.get("osu_user_data"))
        if user is not None:
            login(request, user)
            return Response({"ok": "logged in", "user": user.username})
        return Response({"error": "failed to authenticate"}, status=status.HTTP_401_UNAUTHORIZED)


class OsuAuth(viewsets.ViewSet):
    @action(methods=['get'], detail=False)
    def prompt_login(self, request):
        uri = (f"{settings.OSU_OAUTH_ENDPOINT}/authorize"
               f"?response_type=code"
               f"&client_id={settings.OSU_CLIENT_ID}"
               f"&scope=identify"
               f"&redirect_uri={urllib.parse.quote(OSU_REDIRECT_URI)}"
               f"&prompt=consent")
        return HttpResponseRedirect(redirect_to=uri)

    @action(methods=['get'], detail=False)
    def code(self, request):
        code = request.query_params.get("code", None)
        if code is None:
            return Response({"error": "missing `code` query param"}, status=status.HTTP_400_BAD_REQUEST)

        r = requests.post(f'{settings.OSU_OAUTH_ENDPOINT}/token',
                          data={'grant_type': 'authorization_code',
                                'code': code,
                                'redirect_uri': OSU_REDIRECT_URI},
                          headers={'Content-Type': 'application/x-www-form-urlencoded'},
                          auth=(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET))
        if r.status_code != 200:
            return Response(r.json(), status=r.status_code)

        auth_data = r.json()
        # fetch user information
        r = requests.get(f"{settings.OSU_API_ENDPOINT}/me",
                         headers={"Authorization": f"Bearer {auth_data.get('access_token')}"})
        if r.status_code != 200:
            return Response(r.json(), status=r.status_code)
        user_data = r.json()
        request.session["osu_user_data"] = user_data
        return Response(user_data, status=r.status_code)

    def list(self, request):
        return Response({
            # "a": reverse("some-view-name")
        })


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
        request.session["discord_user_data"] = user_data
        return Response(user_data, status=r.status_code)

        # check if user exists
        # if TournamentPlayer.objects.filter(discord_user_id)

    @action(methods=['get'], detail=False)
    def token(self, request):
        print(request.query_params.get("access_token"))
        return Response(request.query_params)

    def list(self, request):
        return Response({})
