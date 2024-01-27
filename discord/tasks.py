import datetime
import logging

from celery import shared_task
from django.db import transaction

from userauth.authentication import bws, filter_badges, prep_badges_for_db
from userauth.models import TournamentPlayer, TournamentPlayerBadge
from django.core.cache import cache
from django.conf import settings
import requests


logger = logging.getLogger(__name__)


def get_osu_token() -> str | None:
    token_dict = cache.get("osu_token", None)
    if token_dict is None:
        logger.warning("fetching new osu! token")
        r = requests.post("https://osu.ppy.sh/oauth/token", {
            "client_id": settings.OSU_CLIENT_ID,
            "client_secret": settings.OSU_CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "public"
        })
        if r.status_code != 200:
            print(f"[get_osu_token] got status code {r.status_code}")
            cache.delete("osu_token")
            return None
        response_data = r.json()
        cache.set("osu_token", response_data, timeout=response_data['expires_in'] - 30)

        return response_data['access_token']
    return token_dict['access_token']


@shared_task(rate_limit="2/s")  # RATE LIMIT IS PER WORKER -- ONLY RUN ONE WORKER
def update_user(user_id: int):
    logger.info(f"[update_user] looking up user with osu id {user_id}...")
    try:
        tourney_player = TournamentPlayer.objects.get(osu_user_id=user_id)
    except TournamentPlayer.DoesNotExist:
        logger.info(f"[update_user] user with osu id {user_id} not found! Aborting.")
        return

    token = get_osu_token()
    if token is None:
        return

    response = requests.get(f"https://osu.ppy.sh/api/v2/users/{user_id}/osu",
                            headers={"Authorization": f"Bearer {token}"})

    osu_data = response.json()
    all_badges, db_badges = prep_badges_for_db(osu_data, tourney_player)

    tourney_player.osu_rank_std = osu_data['statistics'].get('global_rank', None)
    tourney_player.osu_rank_std_bws = bws(len(filter_badges(all_badges)),
                                          tourney_player.osu_rank_std)
    tourney_player.osu_stats_updated = datetime.datetime.now(tz=datetime.timezone.utc)

    with transaction.atomic():
        # can't be arsed to update, just delete and recreate them all
        TournamentPlayerBadge.objects.filter(user=tourney_player).delete()
        TournamentPlayerBadge.objects.bulk_create(db_badges)
        tourney_player.save()
    try:
        cache.decr("osu_queue_length")
        cache.touch("osu_queue_length", 60)
    except ValueError:
        pass
    logger.info(f"[update_user] {user_id} updated!")


@shared_task
def update_users(user_ids: list[int] | None = None):
    """
    Fetch new statistics for users in user_ids.

    :param user_ids: list of user IDs to update. Defaults to None. If None, update all users in database.
    :return: None
    """

    if user_ids is None:
        all_users = TournamentPlayer.objects.all()
        user_ids = [user.osu_user_id for user in all_users]
    for user_id in user_ids:
        cache.add("osu_queue_length", 0)  # only set if key not already present
        cache.incr("osu_queue_length")
        cache.touch("osu_queue_length", 60)
        logger.debug(f"[update_users] queue now at: {cache.get('osu_queue_length')}")
        update_user.delay(user_id, True)
