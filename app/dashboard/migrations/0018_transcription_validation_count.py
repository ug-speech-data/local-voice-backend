# Generated by Django 4.1.3 on 2023-01-01 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_audio_transcription_count_transcription_is_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='transcription',
            name='validation_count',
            field=models.IntegerField(default=0),
        ),
    ]
