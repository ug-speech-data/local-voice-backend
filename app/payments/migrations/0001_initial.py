# Generated by Django 4.1.3 on 2023-01-23 22:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import payments.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(default=payments.models.Transaction.generate_id, max_length=20, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('paid', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('network', models.CharField(blank=True, max_length=255, null=True)),
                ('fullname', models.CharField(blank=True, max_length=255, null=True)),
                ('response_data', models.TextField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('direction', models.CharField(choices=[('IN', 'IN'), ('OUT', 'OUT')], max_length=10)),
                ('status', models.CharField(blank=True, choices=[('new', 'New'), ('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='new', max_length=255, null=True)),
                ('status_message', models.CharField(blank=True, max_length=255, null=True)),
                ('wallet_balances_updated', models.BooleanField(default=False)),
                ('accepted_by_provider', models.BooleanField(default=False)),
                ('initiated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('wallet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.wallet')),
            ],
            options={
                'db_table': 'transactions',
            },
        ),
    ]
