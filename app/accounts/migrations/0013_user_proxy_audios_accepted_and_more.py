# Generated by Django 4.1.7 on 2023-05-04 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_user_audios_transcribed'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='proxy_audios_accepted',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='proxy_audios_submitted',
            field=models.IntegerField(default=0),
        ),
    ]
