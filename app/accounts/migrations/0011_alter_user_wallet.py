# Generated by Django 4.1.3 on 2023-01-21 16:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_wallet_user_wallet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='wallet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner', to='accounts.wallet'),
        ),
    ]
