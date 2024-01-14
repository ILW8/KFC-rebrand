import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from parameterized import parameterized
from rest_framework.test import APIRequestFactory

from discord.views import TournamentPlayerViewSet
from teammgmt.models import TournamentTeam
from userauth.models import TournamentPlayer, TournamentPlayerBadge


class ReturnBadgesOnDetailViewTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.request_factory = APIRequestFactory()
        self.test_user = User.objects.create()
        self.test_team = TournamentTeam.objects.create(osu_flag="GB")
        self.test_tourney_player = TournamentPlayer.objects.create(
            user_id=self.test_user.pk,
            osu_user_id=self.test_user.pk,
            osu_username=f"user_{self.test_user.pk}",
            discord_user_id=self.test_user.pk,
            osu_stats_updated=datetime.datetime.now(datetime.timezone.utc),
            osu_flag="GB",
            team=self.test_team)

        self.sample_badges = [
            {
                "description": "this user got a badge!",
                "awarded_at": "2023-11-19T21:25:58+00:00",
                "url": "http://testserver/badge",
                "image_url": "http://testserver/image",
                "image_url_2x": "http://testserver/image_2x",
            },
            {
                "description": "this user has _more_ than one badge!!",
                "awarded_at": "2023-11-25T18:51:14+00:00",
                "url": "http://testserver/badge2",
                "image_url": "http://testserver/image2",
                "image_url_2x": "http://testserver/image2_2x",
            },
        ]

    def create_badges_in_db(self, badges):
        for badge in badges:
            TournamentPlayerBadge.objects.create(user=self.test_tourney_player,
                                                 description=badge['description'],
                                                 award_date=datetime.datetime.fromisoformat(badge['awarded_at']),
                                                 url=badge['url'],
                                                 image_url=badge['image_url'],
                                                 image_url_2x=badge['image_url_2x'])

    def test_badges_present_in_details_empty(self):
        request = self.request_factory.get(f'/registrants/{self.test_user.pk}/')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'retrieve'})
        response = registrant_detail(request, pk=self.test_user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.data['badges'], [])

    def create_badge(self, badge_date):
        badges = self.sample_badges.copy()
        badges += [
            {
                "description": "wow, what an old badge!",
                "awarded_at": badge_date,
                "url": "http://testserver/badge_old",
                "image_url": "http://testserver/image_old",
                "image_url_2x": "http://testserver/image_old_2x",
            },
        ]
        return badges

    def prep_request_with_badge_cutoff(self, badge_award_date_str, cutoff_date):
        badges = self.create_badge(badge_award_date_str)
        self.create_badges_in_db(badges)

        cutoff_date_ts = int(cutoff_date.timestamp())
        request = self.request_factory.get(f'/registrants/{self.test_user.pk}/?badge_cutoff_date={cutoff_date_ts}')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'retrieve'})
        response = registrant_detail(request, pk=self.test_user.pk)
        return badges, response

    def test_badges_custom_cutoff_excluded(self):
        award_date = "2019-11-19T21:25:58+00:00"
        cutoff = datetime.datetime.fromisoformat(award_date) + datetime.timedelta(seconds=5)
        badges, response = self.prep_request_with_badge_cutoff(award_date, cutoff)

        self.assertTrue(len(badges) == len(self.sample_badges) + 1)
        self.assertTrue(len(badges) == len(response.data['badges']) + 1)
        self.assertCountEqual(self.sample_badges, response.data['badges'])

    def test_badges_custom_cutoff_included(self):
        award_date = "2019-11-19T21:25:58+00:00"
        cutoff = datetime.datetime.fromisoformat(award_date) + datetime.timedelta(seconds=-5)
        badges, response = self.prep_request_with_badge_cutoff(award_date, cutoff)

        self.assertTrue(len(badges) == len(self.sample_badges) + 1)
        self.assertTrue(len(badges) == len(response.data['badges']))
        self.assertCountEqual(badges, response.data['badges'])

    # noinspection SpellCheckingInspection
    @parameterized.expand([
        ("2020-01-01", ),  # not timestamp
        ("gjkhafgkhadfsg", ),  # not even a date
        ("1705199901.192", ),  # includes fractional part
    ])
    def test_badges_custom_cutoff_invalid_ts(self, invalid_timestamp):
        self.create_badges_in_db(self.sample_badges)

        request = self.request_factory.get(f'/registrants/{self.test_user.pk}/?badge_cutoff_date={invalid_timestamp}')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'retrieve'})
        response = registrant_detail(request, pk=self.test_user.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Invalid badge_cutoff_date provided, please provide a unix timestamp")

    def test_badges_default_cutoff(self):
        badges = self.sample_badges.copy()
        badges += [
            {
                "description": "wow, what an old badge!",
                "awarded_at": "2019-11-19T21:25:58+00:00",
                "url": "http://testserver/badge_old",
                "image_url": "http://testserver/image_old",
                "image_url_2x": "http://testserver/image_old_2x",
            },
        ]
        self.create_badges_in_db(badges)

        request = self.request_factory.get(f'/registrants/{self.test_user.pk}/')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'retrieve'})
        response = registrant_detail(request, pk=self.test_user.pk)

        self.assertTrue(len(badges) == len(self.sample_badges) + 1)
        self.assertTrue(len(badges) == len(response.data['badges']) + 1)
        self.assertEqual(len(self.sample_badges), len(response.data['badges']))
        self.assertCountEqual(self.sample_badges, response.data['badges'])

    def test_badges_present_in_details(self):
        self.create_badges_in_db(self.sample_badges)

        request = self.request_factory.get(f'/registrants/{self.test_user.pk}/')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'retrieve'})
        response = registrant_detail(request, pk=self.test_user.pk)

        self.assertEqual(len(self.sample_badges), len(response.data['badges']))
        self.assertCountEqual(self.sample_badges, response.data['badges'])

    def test_badges_not_present_in_list(self):
        self.create_badges_in_db(self.sample_badges)

        request = self.request_factory.get(f'/registrants/?limit=1')
        registrant_detail = TournamentPlayerViewSet.as_view({'get': 'list'})
        response = registrant_detail(request, pk=self.test_user.pk)
        print(response.data)
