# Generated by Django 4.1.7 on 2023-05-04 01:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_user_proxy_audios_accepted_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='proxy_audios_accepted',
            new_name='proxy_audios_accepted_in_hours',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='proxy_audios_submitted',
            new_name='proxy_audios_submitted_in_hours',
        ),
    ]