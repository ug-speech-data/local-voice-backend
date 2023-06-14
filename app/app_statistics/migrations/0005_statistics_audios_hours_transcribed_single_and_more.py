# Generated by Django 4.1.7 on 2023-06-14 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_statistics', '0004_alter_statistics_akan_audios_approved_in_hours_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='audios_hours_transcribed_single',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name='statistics',
            name='audios_transcribed_single',
            field=models.IntegerField(default=0),
        ),
    ]
