# Generated by Django 4.1.7 on 2023-06-25 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_rename_recording_via_others_benefit_wallet_audios_by_recruits_benefit'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
