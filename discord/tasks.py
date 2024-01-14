from celery import shared_task
from userauth.models import TournamentPlayer


@shared_task(rate_limit="2/s")  # RATE LIMIT IS PER WORKER -- ONLY RUN ONE WORKER
def update_user(user: TournamentPlayer):
    print(f"processing {user}")
    # time.sleep(5)
    print(f"done processing {user}")


@shared_task
def update_users(users: list | None = None):
    # if users is None:
    #     users = TournamentPlayer.objects.all().limit(5)
    if users is None:
        return
    for user in users:
        update_user.delay(user)
