# Generated by Django 4.1.3 on 2023-01-21 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0008_alter_transaction_transaction_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='directions',
            new_name='direction',
        ),
    ]
