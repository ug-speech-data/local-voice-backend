# Generated by Django 4.1.7 on 2023-07-07 07:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0037_audio_second_audio_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audiotranscriptionassignment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_transcription_audios', to=settings.AUTH_USER_MODEL),
        ),
    ]
