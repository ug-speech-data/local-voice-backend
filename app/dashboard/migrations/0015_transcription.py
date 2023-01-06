# Generated by Django 4.1.3 on 2023-01-01 10:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0014_audio_validation_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transcription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('audio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transcriptions', to='dashboard.audio')),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transcriptions', to=settings.AUTH_USER_MODEL)),
                ('validations', models.ManyToManyField(blank=True, related_name='transcription_validations', to='dashboard.validation')),
            ],
        ),
    ]
