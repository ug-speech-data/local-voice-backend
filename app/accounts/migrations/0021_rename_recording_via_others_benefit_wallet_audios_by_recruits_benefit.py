# Generated by Django 4.1.7 on 2023-05-25 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_rename_accepted_audios_submitted_via_others_user_accepted_audios_from_recruits'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wallet',
            old_name='recording_via_others_benefit',
            new_name='audios_by_recruits_benefit',
        ),
    ]