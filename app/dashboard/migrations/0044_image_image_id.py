# Generated by Django 4.1.7 on 2023-10-28 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0043_validation_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='image_id',
            field=models.IntegerField(db_index=True, null=True, unique=True),
        ),
    ]