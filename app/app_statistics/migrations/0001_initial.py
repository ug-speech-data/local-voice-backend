# Generated by Django 4.1.7 on 2023-03-20 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('images_submitted', models.IntegerField(default=0)),
                ('images_approved', models.IntegerField(default=0)),
                ('audios_submitted', models.IntegerField(default=0)),
                ('audios_approved', models.IntegerField(default=0)),
                ('audios_transcribed', models.IntegerField(default=0)),
                ('audios_hours_submitted', models.IntegerField(default=0)),
                ('audios_hours_approved', models.IntegerField(default=0)),
                ('audios_hours_transcribed', models.IntegerField(default=0)),
                ('ewe_audios_submitted', models.IntegerField(default=0)),
                ('ewe_audios_single_validation', models.IntegerField(default=0)),
                ('ewe_audios_double_validation', models.IntegerField(default=0)),
                ('ewe_audios_validation_conflict', models.IntegerField(default=0)),
                ('ewe_audios_approved', models.IntegerField(default=0)),
                ('ewe_audios_transcribed', models.IntegerField(default=0)),
                ('ewe_audios_submitted_in_hours', models.IntegerField(default=0)),
                ('ewe_audios_single_validation_in_hours', models.IntegerField(default=0)),
                ('ewe_audios_double_validation_in_hours', models.IntegerField(default=0)),
                ('ewe_audios_validation_conflict_in_hours', models.IntegerField(default=0)),
                ('ewe_audios_approved_in_hours', models.IntegerField(default=0)),
                ('ewe_audios_transcribed_in_hours', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
