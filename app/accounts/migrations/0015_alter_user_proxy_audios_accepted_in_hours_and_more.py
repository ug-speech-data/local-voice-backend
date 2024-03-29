# Generated by Django 4.1.7 on 2023-05-04 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_rename_proxy_audios_accepted_user_proxy_audios_accepted_in_hours_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='proxy_audios_accepted_in_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AlterField(
            model_name='user',
            name='proxy_audios_submitted_in_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
