# Generated by Django 4.1.7 on 2023-02-27 23:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_audio_api_client_participant_api_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='main_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='dashboard.category'),
        ),
    ]
