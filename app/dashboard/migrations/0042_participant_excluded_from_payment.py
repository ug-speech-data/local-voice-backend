# Generated by Django 4.1.7 on 2023-09-24 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0041_participant_email_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='excluded_from_payment',
            field=models.BooleanField(default=False),
        ),
    ]
