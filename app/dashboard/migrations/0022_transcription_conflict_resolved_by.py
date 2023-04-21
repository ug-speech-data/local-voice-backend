# Generated by Django 4.1.7 on 2023-04-10 19:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0021_transcription_corrected_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='transcription',
            name='conflict_resolved_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transcription_resolutions', to=settings.AUTH_USER_MODEL),
        ),
    ]
