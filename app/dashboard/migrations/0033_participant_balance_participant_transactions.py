# Generated by Django 4.1.7 on 2023-05-08 09:34

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
        ('dashboard', '0032_rename_transcription_count_image_transcription_count_ak_gh_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10),
        ),
        migrations.AddField(
            model_name='participant',
            name='transactions',
            field=models.ManyToManyField(blank=True, null=True, related_name='participants', to='payments.transaction'),
        ),
    ]
