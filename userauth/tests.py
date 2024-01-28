import datetime
from django.test import TestCase
from parameterized import parameterized
from userauth.authentication import filter_badges, bws, DiscordAndOsuAuthBackend
from rest_framework.test import APIRequestFactory
from django.contrib.auth import authenticate

from userauth.models import DisqualifiedUser
from userauth.views import DiscordAuth, OsuAuth, SessionDetails


class NoOpAuthEndpointsTestCase(TestCase):
    def test_osu_auth_list_empty(self):
        factory = APIRequestFactory()
        osu_auth_view = OsuAuth.as_view({'get': 'list'})
        response = osu_auth_view(factory.get('/auth/osu/'))
        self.assertDictEqual({"727": "when you see it"}, response.data)

    def test_discord_auth_list_empty(self):
        factory = APIRequestFactory()
        discord_auth_view = DiscordAuth.as_view({'get': 'list'})
        response = discord_auth_view(factory.get('/auth/discord/'))
        self.assertDictEqual({"727": "when you see it"}, response.data)


class DiscordAndOsuLoginTestCase(TestCase):
    @parameterized.expand([
        ({}, {}),
        (None, {}),
        ({}, None),
        (None, None),
    ])
    def test_login_fail(self, discord_user_data, osu_user_data):
        factory = APIRequestFactory()
        req = factory.get('/auth/session/login/')
        user = authenticate(req,
                            discord_user_data=discord_user_data,
                            osu_user_data=osu_user_data)
        self.assertIsNone(user)

    # this is so dumb
    def test_dq_model_stringify(self):
        dq_user = DisqualifiedUser.objects.create(osu_user_id=1234727)
        self.assertEqual(f"https://osu.ppy.sh/users/{dq_user.osu_user_id}", str(dq_user))

    def test_login_disqualified_user(self):
        factory = APIRequestFactory()
        req = factory.get('/auth/session/login/')

        dq_user_id = 1234727
        DisqualifiedUser.objects.get_or_create(osu_user_id=dq_user_id)
        req.session = {"osu_user_data": {"id": dq_user_id}, "discord_user_data": {}}
        session_login_view = SessionDetails.as_view({'get': 'login'})
        response = session_login_view(req)
        self.assertEqual(403, response.status_code)
        self.assertEqual("user disqualified", response.data["error"])

    def test_login_not_disqualified_user(self):
        factory = APIRequestFactory()
        req = factory.get('/auth/session/login/')

        dq_user_id = 1234727
        req.session = {"osu_user_data": {"id": dq_user_id}, "discord_user_data": {}}
        session_login_view = SessionDetails.as_view({'get': 'login'})
        response = session_login_view(req)
        self.assertNotEqual("user disqualified", response.data["error"])

    def test_login_no_session(self):
        factory = APIRequestFactory()
        req = factory.get('/auth/session/login/')
        req.session = {}
        session_login_view = SessionDetails.as_view({'get': 'login'})
        response = session_login_view(req)
        self.assertEqual(401, response.status_code)
        self.assertEqual("required discord or osu! session missing", response.data["msg"])

    @parameterized.expand([
        ({'id': "874598213518214312", 'username': 'jame', 'discriminator': '0443'}, 'jame#0443'),
        ({'id': "109274120794127402", 'username': 'james', 'discriminator': '0'}, 'james'),
        ({"id": "832597585923014676", "username": "Yuna", "discriminator": "0112"}, 'Yuna#0112')
    ])
    def test_parse_discord_composite_username(self, discord_user_data, expected):
        validated_discord_data, _ = DiscordAndOsuAuthBackend.validate_data(discord_user_data, {})
        self.assertIsNotNone(validated_discord_data)
        self.assertEqual(expected, validated_discord_data['composite_username'])

    @parameterized.expand([
        (1292,
         1235,
         {'id': 2155578,
          'username': 'Azer',
          'country_code': 'CA',
          'statistics': {"global_rank": 1292},
          'badges': [
              {
                  "awarded_at": "2023-11-19T21:25:58+00:00",
                  "description": "Outstanding contribution to the osu! tournament scene and the World Cups",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/contributor@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/contributor.png",
                  "url": "https://osu.ppy.sh/wiki/en/People/Community_Contributors"
              },
              {
                  "awarded_at": "2023-07-16T19:44:58+00:00",
                  "description": "Longstanding commitment to World Cup Commentary (6 years)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6.png",
                  "url": "https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups"
              },
              {
                  "awarded_at": "2023-07-16T19:43:11+00:00",
                  "description": "Longstanding commitment to World Cup Pooling (3 years)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/pooling-3@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/pooling-3.png",
                  "url": "https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups"
              },
              {
                  "awarded_at": "2023-07-16T19:42:42+00:00",
                  "description": "Longstanding commitment to World Cup Organisation (3 years)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/organiser-3@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/tournament-helpers/organiser-3.png",
                  "url": "https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups"
              },
              {
                  "awarded_at": "2023-04-30T11:49:15+00:00",
                  "description": "Spring Flower Scramble: Wisteria Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/sfswis-2023@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/sfswis-2023.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1717112"
              },
              {
                  "awarded_at": "2023-01-19T02:08:46+00:00",
                  "description": "Mapper's Choice Awards 2021: Top 3 in the user/beatmap category Hitsounding",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021@2x.png?2023-01-20",
                  "image_url": "https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021.png?2023-01-20",
                  "url": "https://mca.corsace.io/2021/results"
              },
              {
                  "awarded_at": "2020-12-06T19:38:15+00:00",
                  "description": "osu! World Cup 2020 3rd Place (Canada)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd.png",
                  "url": "https://osu.ppy.sh/wiki/en/Tournaments/OWC/2020"
              },
              {
                  "awarded_at": "2020-04-21T09:55:41+00:00",
                  "description": "osu! TV Size Tournament 2020 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/otst-2020@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/otst-2020.png",
                  "url": ""
              },
              {
                  "awarded_at": "2019-02-23T05:54:20+00:00",
                  "description": "SST Summer 2018 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ssts-2018@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/ssts-2018.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-09-24T11:44:46+00:00",
                  "description": "OWCT 2018 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ocwt10-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ocwt10-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-06T11:21:11+00:00",
                  "description": "Z-Tournament 2018 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/z-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/z-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-06-18T12:39:18+00:00",
                  "description": "OTC2 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/otc2-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/otc2-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-05-07T02:32:09+00:00",
                  "description": "OTST 2018 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/otst-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/otst-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-02-14T08:28:21+00:00",
                  "description": "SMT Winter 2018 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/smtw-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/smtw-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2017-11-24T02:58:50+00:00",
                  "description": "OHC 2017 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ohc-2017@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ohc-2017.png",
                  "url": ""
              },
              {
                  "awarded_at": "2017-09-11T09:56:14+00:00",
                  "description": "osu! Maple Cup 2017 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/maplecup-2017@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/maplecup-2017.png",
                  "url": ""
              },
              {
                  "awarded_at": "2017-08-27T12:25:07+00:00",
                  "description": "Z-Tournament 2017 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ozt-2017@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ozt-2017.png",
                  "url": ""
              },
              {
                  "awarded_at": "2017-03-10T07:39:19+00:00",
                  "description": "SMT Winter 2017 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/smtw-2017@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/smtw-2017.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/496953?n=1"
              },
              {
                  "awarded_at": "2016-11-02T10:50:41+00:00",
                  "description": "Maple Cup 2016 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/maple-cup-champion@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/maple-cup-champion.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/487098?n=1"
              },
              {
                  "awarded_at": "2015-09-30T02:27:42+00:00",
                  "description": "Maple Cup 2015 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/MC2015@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/MC2015.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/351395?n=1"
              },
              {
                  "awarded_at": "2014-08-12T15:08:35+00:00",
                  "description": "North American Tournament (Winner)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/nat2014@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/nat2014.jpg",
                  "url": ""
              }
          ]}),
        (13254,
         10458,
         {'id': 3257847,
          'username': 'MyzeJD',
          'country_code': 'FR',
          'statistics': {"global_rank": 13254},
          "badges": [
              {
                  "awarded_at": "2023-08-27T05:40:28+00:00",
                  "description": "MonkeCup 4 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/mc4@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/mc4.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1761132"
              },
              {
                  "awarded_at": "2023-04-30T11:47:57+00:00",
                  "description": "5 Digit World Cup 2023 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/5dwc-2023@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/5dwc-2023.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1699537"
              }
          ]}),
        (11449,
         9067,
         {'id': 9878349,
          'username': 'FILIPINO',
          'country_code': 'US',
          'statistics': {"global_rank": 11449},
          "badges": [
              {
                  "awarded_at": "2023-01-02T04:23:55+00:00",
                  "description": "CES Gaming osu! Intermediate 2022 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ointm-2022@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ointm-2022.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1623183?n=1"
              },
              {
                  "awarded_at": "2022-10-08T03:47:42+00:00",
                  "description": "5 Digit North American Duos 2022 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/5dna-2022@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/5dna-2022.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1604247?n=1"
              }
          ]}),
        (4701,
         4701,
         {'id': 2609349,
          'username': 'Weed',
          'country_code': 'US',
          'statistics': {"global_rank": 4701},
          "badges": [
              {
                  "awarded_at": "2019-09-02T04:39:32+00:00",
                  "description": "osu! Global Tournament 5 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ogt5-2019@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ogt5-2019.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-10-29T06:35:05+00:00",
                  "description": "Old Map Fantasy Tournament 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/omf2-2018@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/omf2-2018.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-09-24T11:44:37+00:00",
                  "description": "Enigmatic Summer Solstice Tier 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ess-t2-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ess-t2-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-28T14:03:35+00:00",
                  "description": "osu! Global Tournament 4 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ogt4-2018@2x.png?resize",
                  "image_url": "https://assets.ppy.sh/profile-badges/ogt4-2018.png?resize",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-28T14:03:31+00:00",
                  "description": "Corn Cup 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/cc2-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/cc2-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-06T11:21:18+00:00",
                  "description": "osu! Tandem Tournament 2 Winning Team (10k-25k)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ott2-10k25k-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ott2-10k25k-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-05-07T02:32:01+00:00",
                  "description": "Arcanus New Year Blast 2018 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/nyb18-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/nyb18-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-04-16T21:17:58+00:00",
                  "description": "ENYT 2018 Tier 1 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/enyt-t1-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/enyt-t1-2018.png",
                  "url": ""
              }
          ]}),
        (10075,
         10075,
         {'id': 3318654,
          'username': 'Fish-',
          'country_code': 'US',
          'statistics': {"global_rank": 10075},
          "badges": [
              {
                  "awarded_at": "2019-10-14T04:24:51+00:00",
                  "description": "Lobby 42: Anti Carry Tournament Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/l42act-2019@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/l42act-2019.png",
                  "url": ""
              },
              {
                  "awarded_at": "2019-08-04T10:09:14+00:00",
                  "description": "Villoux Tournament #3 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/v3-2019@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/v3-2019.png",
                  "url": ""
              },
              {
                  "awarded_at": "2019-05-13T12:00:11+00:00",
                  "description": "osu! Redemption Tournament 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ort2-2019@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ort2-2019.png",
                  "url": ""
              },
              {
                  "awarded_at": "2019-04-25T04:46:41+00:00",
                  "description": "nik's Winter Tour 2019 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/nwt-2019@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/nwt-2019.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-12-15T07:23:18+00:00",
                  "description": "Cindelluna’s Autumn Tour 2018 10k - 19k Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/cat-10k19k-2018@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/cat-10k19k-2018.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-11-28T05:26:59+00:00",
                  "description": "RHOC Ex Cup Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/rhoc-2018@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/rhoc-2018.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-10-29T06:35:04+00:00",
                  "description": "Old Map Fantasy Tournament 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/omf2-2018@2x.jpg",
                  "image_url": "https://assets.ppy.sh/profile-badges/omf2-2018.jpg",
                  "url": ""
              },
              {
                  "awarded_at": "2018-09-24T11:44:37+00:00",
                  "description": "Enigmatic Summer Solstice Tier 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ess-t2-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ess-t2-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-28T14:03:36+00:00",
                  "description": "osu! Global Tournament 4 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ogt4-2018@2x.png?resize",
                  "image_url": "https://assets.ppy.sh/profile-badges/ogt4-2018.png?resize",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-28T14:03:33+00:00",
                  "description": "Project Rekindling Summer 2018 7k-18k Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/prk-2018-718k@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/prk-2018-718k.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-08-06T11:21:19+00:00",
                  "description": "osu! Tandem Tournament 2 Winning Team (10k-25k)",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ott2-10k25k-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ott2-10k25k-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2018-06-12T10:15:51+00:00",
                  "description": "Re:Tourney 2018 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/retourney-2018@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/retourney-2018.png",
                  "url": ""
              },
              {
                  "awarded_at": "2017-12-19T08:44:51+00:00",
                  "description": "Five Digit Division Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/fdd-2017@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/fdd-2017.png",
                  "url": ""
              }
          ]}),
        (14226,
         5671,
         {'id': 2504750,
          'username': 'Varler',
          'country_code': 'US',
          'statistics': {"global_rank": 14226},
          "badges": [
              {
                  "awarded_at": "2023-03-30T07:08:21+00:00",
                  "description": "Americas Draft Showdown 2023 Division 2 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ads-d2-2023@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ads-d2-2023.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1705194"
              },
              {
                  "awarded_at": "2022-03-28T08:39:41+00:00",
                  "description": "American Draft Showdown 2022 Division II Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/ads-t2-2022@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/ads-t2-2022.png",
                  "url": "https://osu.ppy.sh/community/forums/topics/1505437?n=1"
              },
              {
                  "awarded_at": "2021-03-15T12:21:10+00:00",
                  "description": "osu! Heroes 2021 Winning Team",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/oheroes-2021@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/oheroes-2021.png",
                  "url": ""
              },
              {
                  "awarded_at": "2021-01-01T10:28:58+00:00",
                  "description": "Villoux Tournament #7 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/villoux7-2020@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/villoux7-2020.png",
                  "url": ""
              },
              {
                  "awarded_at": "2020-12-15T08:19:07+00:00",
                  "description": "Dio's Autumn Singles Tier 3 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/dios-t3-2020@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/dios-t3-2020.png",
                  "url": ""
              },
              {
                  "awarded_at": "2020-08-07T02:11:32+00:00",
                  "description": "Villoux Tournament #6 Winner",
                  "image@2x_url": "https://assets.ppy.sh/profile-badges/vill6-2020@2x.png",
                  "image_url": "https://assets.ppy.sh/profile-badges/vill6-2020.png",
                  "url": ""
              }
          ]}),
    ])
    def test_authenticate_populate_osu_stats(self, global_rank, expected_bws, osu_data):
        valid_discord_data = {"id": "0", "username": "0", "discriminator": "0"}

        factory = APIRequestFactory()
        req = factory.get('/auth/session/login/')
        user = authenticate(req,
                            discord_user_data=valid_discord_data,
                            osu_user_data=osu_data)
        self.assertIsNotNone(user)
        self.assertEqual(global_rank, user.tournamentplayer.osu_rank_std)
        self.assertEqual(expected_bws, user.tournamentplayer.osu_rank_std_bws)


class BadgeWeightedSeedingCalculationTestCase(TestCase):
    @parameterized.expand([
        (5, 832141, 113493),
        (1, 28151, 26391),
        (1, 27817, 26080),
        (1, 10601, 10000),
        (0, 42387, 42387),
        (0, 2319784, 2319784),
        (0, 69727, 69727),
        (1, 69727, 64996),
        (2, 69727, 52783),
        (3, 69727, 37636),
        (4, 69727, 23856),
        (5, 69727, 13663),
        (6, 69727, 7208),
        (7, 69727, 3577),
        (8, 69727, 1707),
        (9, 69727, 800),
        (10, 69727, 375),
        (32, 69727, 1),
    ])
    def test_bws(self, badges: int, global_rank: int, expected_bws: int):
        bws_seed = bws(badges, global_rank)
        self.assertEqual(bws_seed, expected_bws)


class BadgeFilterTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None

    @parameterized.expand([
        ("mappers_choice_award",
         [{'awarded_at': '2023-01-19T02:08:46+00:00',
           'description': "Mapper's Choice Awards 2021: Top 3 in the user/beatmap category Hitsounding",
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021@2x.png?2023-01-20',
           'image_url': 'https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021.png?2023-01-20',
           'url': 'https://mca.corsace.io/2021/results'}],
         []),
        ("world_cup_longstanding",
         [{'awarded_at': '2023-07-16T19:44:58+00:00',
           'description': 'Longstanding commitment to World Cup Commentary (6 years)',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6.png',
           'url': 'https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups'}],
         []),
        ("world_cup_outstanding",
         [{'awarded_at': '2023-11-19T21:25:58+00:00',
           'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
           'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'}],
         []),
        ("world_cup_win",
         [{
             "awarded_at": "2020-12-06T19:38:15+00:00",
             "description": "osu! World Cup 2020 3rd Place (Canada)",
             "image@2x_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd@2x.png",
             "image_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd.png",
             "url": "https://osu.ppy.sh/wiki/en/Tournaments/OWC/2020"
         }],
         [{
             "awarded_at": "2020-12-06T19:38:15+00:00",
             "description": "osu! World Cup 2020 3rd Place (Canada)",
             "image@2x_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd@2x.png",
             "image_url": "https://assets.ppy.sh/profile-badges/badge_owc2020_3rd.png",
             "url": "https://osu.ppy.sh/wiki/en/Tournaments/OWC/2020"
         }])
    ])
    def test_filter_bws_strings(self, _, badges, expected):
        """
        example with Azer (2155578)

        expected = [
            {'awarded_at': '2023-04-30T11:49:15+00:00',
             'description': 'Spring Flower Scramble: Wisteria Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/sfswis-2023@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/sfswis-2023.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/1717112'},
            {'awarded_at': '2020-12-06T19:38:15+00:00', 'description': 'osu! World Cup 2020 3rd Place (Canada)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/badge_owc2020_3rd@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/badge_owc2020_3rd.png',
             'url': 'https://osu.ppy.sh/wiki/en/Tournaments/OWC/2020'},
            {'awarded_at': '2020-04-21T09:55:41+00:00',
             'description': 'osu! TV Size Tournament 2020 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otst-2020@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otst-2020.png', 'url': ''},
            {'awarded_at': '2019-02-23T05:54:20+00:00', 'description': 'SST Summer 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ssts-2018@2x.jpg',
             'image_url': 'https://assets.ppy.sh/profile-badges/ssts-2018.jpg', 'url': ''},
            {'awarded_at': '2018-09-24T11:44:46+00:00', 'description': 'OWCT 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ocwt10-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ocwt10-2018.png', 'url': ''},
            {'awarded_at': '2018-08-06T11:21:11+00:00', 'description': 'Z-Tournament 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/z-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/z-2018.png', 'url': ''},
            {'awarded_at': '2018-06-18T12:39:18+00:00', 'description': 'OTC2 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otc2-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otc2-2018.png', 'url': ''},
            {'awarded_at': '2018-05-07T02:32:09+00:00', 'description': 'OTST 2018 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otst-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otst-2018.png', 'url': ''},
            {'awarded_at': '2018-02-14T08:28:21+00:00', 'description': 'SMT Winter 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/smtw-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/smtw-2018.png', 'url': ''},
            {'awarded_at': '2017-11-24T02:58:50+00:00', 'description': 'OHC 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ohc-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ohc-2017.png', 'url': ''},
            {'awarded_at': '2017-09-11T09:56:14+00:00', 'description': 'osu! Maple Cup 2017 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/maplecup-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/maplecup-2017.png', 'url': ''},
            {'awarded_at': '2017-08-27T12:25:07+00:00', 'description': 'Z-Tournament 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ozt-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ozt-2017.png', 'url': ''},
            {'awarded_at': '2017-03-10T07:39:19+00:00', 'description': 'SMT Winter 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/smtw-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/smtw-2017.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/496953?n=1'},
            {'awarded_at': '2016-11-02T10:50:41+00:00', 'description': 'Maple Cup 2016 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/maple-cup-champion@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/maple-cup-champion.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/487098?n=1'},
            {'awarded_at': '2015-09-30T02:27:42+00:00', 'description': 'Maple Cup 2015 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/MC2015@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/MC2015.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/351395?n=1'},
            {'awarded_at': '2014-08-12T15:08:35+00:00', 'description': 'North American Tournament (Winner)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/nat2014@2x.jpg',
             'image_url': 'https://assets.ppy.sh/profile-badges/nat2014.jpg', 'url': ''}
        ]
        badges = [
            {'awarded_at': '2023-11-19T21:25:58+00:00',
             'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
             'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'},
            {'awarded_at': '2023-07-16T19:44:58+00:00',
             'description': 'Longstanding commitment to World Cup Commentary (6 years)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/commentary-6.png',
             'url': 'https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups'},
            {'awarded_at': '2023-07-16T19:43:11+00:00',
             'description': 'Longstanding commitment to World Cup Pooling (3 years)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/pooling-3@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/pooling-3.png',
             'url': 'https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups'},
            {'awarded_at': '2023-07-16T19:42:42+00:00',
             'description': 'Longstanding commitment to World Cup Organisation (3 years)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/organiser-3@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/tournament-helpers/organiser-3.png',
             'url': 'https://osu.ppy.sh/wiki/en/Tournaments#official-world-cups'},
            {'awarded_at': '2023-04-30T11:49:15+00:00',
             'description': 'Spring Flower Scramble: Wisteria Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/sfswis-2023@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/sfswis-2023.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/1717112'},
            {'awarded_at': '2023-01-19T02:08:46+00:00',
             'description': "Mapper's Choice Awards 2021: Top 3 in the user/beatmap category Hitsounding",
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021@2x.png?2023-01-20',
             'image_url': 'https://assets.ppy.sh/profile-badges/mca-2022/mca-standard-2021.png?2023-01-20',
             'url': 'https://mca.corsace.io/2021/results'},
            {'awarded_at': '2020-12-06T19:38:15+00:00', 'description': 'osu! World Cup 2020 3rd Place (Canada)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/badge_owc2020_3rd@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/badge_owc2020_3rd.png',
             'url': 'https://osu.ppy.sh/wiki/en/Tournaments/OWC/2020'},
            {'awarded_at': '2020-04-21T09:55:41+00:00',
             'description': 'osu! TV Size Tournament 2020 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otst-2020@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otst-2020.png', 'url': ''},
            {'awarded_at': '2019-02-23T05:54:20+00:00', 'description': 'SST Summer 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ssts-2018@2x.jpg',
             'image_url': 'https://assets.ppy.sh/profile-badges/ssts-2018.jpg', 'url': ''},
            {'awarded_at': '2018-09-24T11:44:46+00:00', 'description': 'OWCT 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ocwt10-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ocwt10-2018.png', 'url': ''},
            {'awarded_at': '2018-08-06T11:21:11+00:00', 'description': 'Z-Tournament 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/z-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/z-2018.png', 'url': ''},
            {'awarded_at': '2018-06-18T12:39:18+00:00', 'description': 'OTC2 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otc2-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otc2-2018.png', 'url': ''},
            {'awarded_at': '2018-05-07T02:32:09+00:00', 'description': 'OTST 2018 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/otst-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/otst-2018.png', 'url': ''},
            {'awarded_at': '2018-02-14T08:28:21+00:00', 'description': 'SMT Winter 2018 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/smtw-2018@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/smtw-2018.png', 'url': ''},
            {'awarded_at': '2017-11-24T02:58:50+00:00', 'description': 'OHC 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ohc-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ohc-2017.png', 'url': ''},
            {'awarded_at': '2017-09-11T09:56:14+00:00', 'description': 'osu! Maple Cup 2017 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/maplecup-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/maplecup-2017.png', 'url': ''},
            {'awarded_at': '2017-08-27T12:25:07+00:00', 'description': 'Z-Tournament 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/ozt-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/ozt-2017.png', 'url': ''},
            {'awarded_at': '2017-03-10T07:39:19+00:00', 'description': 'SMT Winter 2017 Winning Team',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/smtw-2017@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/smtw-2017.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/496953?n=1'},
            {'awarded_at': '2016-11-02T10:50:41+00:00', 'description': 'Maple Cup 2016 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/maple-cup-champion@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/maple-cup-champion.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/487098?n=1'},
            {'awarded_at': '2015-09-30T02:27:42+00:00', 'description': 'Maple Cup 2015 Winner',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/MC2015@2x.png',
             'image_url': 'https://assets.ppy.sh/profile-badges/MC2015.png',
             'url': 'https://osu.ppy.sh/community/forums/topics/351395?n=1'},
            {'awarded_at': '2014-08-12T15:08:35+00:00', 'description': 'North American Tournament (Winner)',
             'image@2x_url': 'https://assets.ppy.sh/profile-badges/nat2014@2x.jpg',
             'image_url': 'https://assets.ppy.sh/profile-badges/nat2014.jpg', 'url': ''}
        ]
        :param badges:
        :param expected:
        :return:
        """
        filtered_badges = filter_badges(badges,
                                        cutoff_date=datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc))
        self.assertCountEqual(filtered_badges, expected)

    @parameterized.expand([
        ("default_cutoff_ok",
         None,
         [{'awarded_at': '2023-11-19T21:25:58+00:00',
           'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
           'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'}],
         [{'awarded_at': '2023-11-19T21:25:58+00:00',
           'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
           'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'}]),
        ("default_cutoff_filtered",
         None,
         [{'awarded_at': '2019-12-31T23:25:58+00:00',
           'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
           'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'}],
         []),
        ("custom_cutoff_filtered",
         datetime.datetime(2023, 12, 1, tzinfo=datetime.timezone.utc),
         [{'awarded_at': '2023-11-19T21:25:58+00:00',
           'description': 'Outstanding contribution to the osu! tournament scene and the World Cups',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/contributor@2x.png',
           'image_url': 'https://assets.ppy.sh/profile-badges/contributor.png',
           'url': 'https://osu.ppy.sh/wiki/en/People/Community_Contributors'}],
         []),
        ("custom_cutoff_ok",
         datetime.datetime(2014, 8, 1, tzinfo=datetime.timezone.utc),
         [{'awarded_at': '2014-08-12T15:08:35+00:00', 'description': 'North American Tournament (Winner)',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/nat2014@2x.jpg',
           'image_url': 'https://assets.ppy.sh/profile-badges/nat2014.jpg', 'url': ''}],
         [{'awarded_at': '2014-08-12T15:08:35+00:00', 'description': 'North American Tournament (Winner)',
           'image@2x_url': 'https://assets.ppy.sh/profile-badges/nat2014@2x.jpg',
           'image_url': 'https://assets.ppy.sh/profile-badges/nat2014.jpg', 'url': ''}])
    ])
    def test_filter_bws_cutoff_date(self, _, cutoff_date, badges, expected):
        if cutoff_date is None:
            filtered_badges = filter_badges(badges, [])
        else:
            filtered_badges = filter_badges(badges, [], cutoff_date=cutoff_date)
        self.assertCountEqual(filtered_badges, expected)
