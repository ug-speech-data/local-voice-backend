# Generated by Django 4.1.7 on 2023-04-22 11:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('setup', '0012_remove_appconfiguration_api_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfiguration',
            name='default_user_group',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
    ]
