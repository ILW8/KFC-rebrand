# Generated by Django 4.2.6 on 2024-02-08 03:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0015_disqualifieduser'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournamentplayer',
            name='is_captain',
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL('ALTER TABLE userauth_tournamentplayer ALTER COLUMN is_captain SET DEFAULT 0;'),
        migrations.AddConstraint(
            model_name='tournamentplayer',
            constraint=models.CheckConstraint(check=models.Q(('in_roster', False), ('is_captain', True), _negated=True), name='captain_only_if_also_in_roster'),
        ),
    ]
