# Generated by Django 4.1.7 on 2023-03-23 16:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0013_alter_participant_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='audio',
            name='conflict_resolved_by',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='resolutions', to=settings.AUTH_USER_MODEL),
        ),
    ]
