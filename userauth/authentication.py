import datetime
import json
import math
from typing import Iterable

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from teammgmt.models import TournamentTeam
from userauth.models import TournamentPlayer, TournamentPlayerBadge

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

FILTER_PHRASES = {"contrib", "nomination", "assessment", "moderation", "spotlight", "mapper", "mapping", "aspire",
                  "monthly", "exemplary", "outstanding", "longstanding", "idol", "pending", "gmt", "global moderators",
                  "trivium", "pickem", "fanart", "fan art", "skinning", "labour of love", "community choice",
                  "community favourite", "mania", "taiko", "catch"}


def filter_badges(badges: list[dict],
                  filter_phrases: Iterable[str] = None,
                  cutoff_date=datetime.datetime(2021, 1, 1, 0, 0, 0,
                                                tzinfo=datetime.timezone.utc)):
    if filter_phrases is None:
        filter_phrases = FILTER_PHRASES
    return [badge for badge in badges
            if not any([word.lower() in badge['description'].lower() for word in filter_phrases])
            and (cutoff_date is None or datetime.datetime.fromisoformat(badge['awarded_at']) > cutoff_date)]


def prep_badges_for_db(osu_data, tourney_player):
    # cutoff_date date of 0 timestamp to keep all badges in DB
    all_badges = filter_badges(osu_data['badges'],
                               cutoff_date=datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc))
    db_badges = [TournamentPlayerBadge(user=tourney_player,
                                       description=badge['description'],
                                       award_date=datetime.datetime.fromisoformat(badge['awarded_at']),
                                       url=badge['url'],
                                       image_url=badge['image_url'],
                                       image_url_2x=badge['image@2x_url'])
                 for badge in all_badges]
    return all_badges, db_badges


def bws(badges_count: int, global_rank: int) -> int:
    """
    BWS = global_rank ^ (0.9937 ^ (badge_count ^ 2))
    :param badges_count: number of eligible badges
    :param global_rank: current global rank
    :return: int
    """
    return round(
        math.pow(
            global_rank,
            math.pow(
                0.9937,
                badges_count ** 2
            )
        )
    )


class DiscordAndOsuAuthBackend(BaseBackend):
    @staticmethod
    def validate_data(discord_user_data, osu_user_data):
        if discord_user_data is None or osu_user_data is None:
            return None, None

        discord_data = {'id': None, 'username': None, 'discriminator': None}
        for key in discord_data:
            discord_data[key] = discord_user_data.get(key)
        if None in discord_data.values():  # ensure all fields filled
            discord_data = None
        if discord_data is not None:
            discord_data['composite_username'] = discord_data['username']
            discord_data['composite_username'] += f"#{discord_data['discriminator']}" \
                if discord_data['discriminator'] != '0' \
                else ''

        osu_data = {'id': None, 'username': None, 'country_code': None, 'statistics': None, 'badges': None}
        for key in osu_data:
            osu_data[key] = osu_user_data.get(key)
        if None in osu_data.values():
            osu_data = None
        return discord_data, osu_data

    # todo: split user creation from authentication
    def authenticate(self, request, discord_user_data=None, osu_user_data=None):
        discord_data, osu_data = self.validate_data(discord_user_data, osu_user_data)
        if discord_data is None or osu_data is None:
            return None

        username = f"{discord_data['id']}.{osu_data['id']}"
        try:
            # check both user and TournamentPlayer exist
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                # found existing TournamentPlayer with different discord id
                tournament_player: TournamentPlayer = TournamentPlayer.objects.filter(osu_user_id=osu_data['id'])[0]
                old_discord_id = tournament_player.discord_user_id

                tournament_player.discord_user_id = discord_data['id']
                tournament_player.discord_username = discord_data['composite_username']
                tournament_player.user.username = username
                tournament_player.user.save()
                tournament_player.save()
                try:
                    channel_layer = get_channel_layer()
                    # noinspection PyArgumentList
                    async_to_sync(channel_layer.group_send)(
                        settings.CHANNELS_DISCORD_WS_GROUP_NAME,
                        {
                            "type": "registration.discord.switch",
                            "message": json.dumps({
                                "old_discord_user_id": old_discord_id,
                                "new_discord_user_id": tournament_player.discord_user_id,
                                "action": "discord_switch"
                            })
                        })
                finally:
                    return tournament_player.user
            except IndexError:
                pass

            # Create a new user. There's no need to set a password
            # because only the password from settings.py is checked.
            user = User(username=username, is_staff=False, is_superuser=False)
            user.save()

        try:
            TournamentPlayer.objects.get(discord_user_id=discord_data['id'], osu_user_id=osu_data['id'])
        except TournamentPlayer.DoesNotExist:

            # create tournament player
            tournament_team, _ = TournamentTeam.objects.get_or_create(osu_flag=osu_data['country_code'])
            tourney_player = TournamentPlayer(user=user,
                                              discord_user_id=discord_data['id'],
                                              discord_username=discord_data['composite_username'],
                                              osu_user_id=osu_data['id'],
                                              osu_username=osu_data['username'],
                                              osu_flag=osu_data['country_code'],
                                              team=tournament_team,
                                              # global_rank can be null, but I'm not sure if global_rank is
                                              # always present
                                              osu_rank_std=osu_data['statistics'].get('global_rank', None),
                                              osu_stats_updated=datetime.datetime.now(datetime.timezone.utc))

            # save user badges
            all_badges, db_badges = prep_badges_for_db(osu_data, tourney_player)

            TournamentPlayerBadge.objects.bulk_create(db_badges)

            # filter again to filter by cutoff date, calculate BWS
            tourney_player.osu_rank_std_bws = bws(len(filter_badges(all_badges)),
                                                  tourney_player.osu_rank_std)
            tourney_player.save()

            channel_layer = get_channel_layer()
            # noinspection PyArgumentList
            async_to_sync(channel_layer.group_send)(
                settings.CHANNELS_DISCORD_WS_GROUP_NAME,
                {
                    "type": "registration.new",
                    "message": json.dumps({"discord_user_id": tourney_player.discord_user_id,
                                           "osu_user_id": tourney_player.osu_user_id,
                                           "osu_username": tourney_player.osu_username,
                                           "osu_global_rank": tourney_player.osu_rank_std,
                                           "osu_global_rank_bws": tourney_player.osu_rank_std_bws,
                                           "flag": tourney_player.osu_flag,
                                           "is_organizer": tourney_player.is_organizer,
                                           "action": "register"})
                })
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
