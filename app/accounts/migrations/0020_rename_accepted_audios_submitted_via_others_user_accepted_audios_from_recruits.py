# Generated by Django 4.1.7 on 2023-05-25 20:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_rename_audios_submitted_via_others_user_accepted_audios_submitted_via_others'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='accepted_audios_submitted_via_others',
            new_name='accepted_audios_from_recruits',
        ),
    ]
