# Generated by Django 4.1.3 on 2022-12-31 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_image_validation_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='source_url',
            field=models.URLField(blank=True, null=True, unique=True),
        ),
    ]
