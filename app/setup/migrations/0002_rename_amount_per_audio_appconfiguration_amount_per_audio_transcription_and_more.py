# Generated by Django 4.1.3 on 2023-02-07 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appconfiguration',
            old_name='amount_per_audio',
            new_name='amount_per_audio_transcription',
        ),
        migrations.AddField(
            model_name='appconfiguration',
            name='amount_per_audio_validation',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='appconfiguration',
            name='audio_aggregators_amount_per_audio',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='appconfiguration',
            name='individual_audio_aggregators_amount_per_audio',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='appconfiguration',
            name='participant_amount_per_audio',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
