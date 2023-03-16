# Generated by Django 4.1.7 on 2023-03-16 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0007_appconfiguration_number_of_audios_per_participant'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfiguration',
            name='max_audio_validation_per_user',
            field=models.IntegerField(default=12000),
        ),
    ]
