from django.urls import path, include
from rest_framework import routers
from . import views


router = routers.DefaultRouter()
# router.register('discord_login', views.first_thing)
router.register('discord', views.DiscordAuth, basename='discord_code')
# router.register('users', views.UserViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
