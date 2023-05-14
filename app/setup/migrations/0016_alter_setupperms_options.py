# Generated by Django 4.1.7 on 2023-05-14 01:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0015_appconfiguration_hours_to_keep_audios_for_transcription'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='setupperms',
            options={'default_permissions': (), 'managed': False, 'permissions': [('manage_setup', 'Can manage system setup'), ('validate_image', 'Can validate image'), ('validate_audio', 'Can validate audio'), ('transcribe_audio', 'Can transcribe audio'), ('validate_transcription', 'Can validate transcription'), ('resolve_transcription', 'Can resolve transcription'), ('manage_collected_data', 'Can manage collected data'), ('manage_payment', 'Can manage payments'), ('record_self', 'Can record oneself'), ('record_others', 'Can record others'), ('approve_sample_audio_recorders', 'Can approve sample audio recorders')]},
        ),
    ]
