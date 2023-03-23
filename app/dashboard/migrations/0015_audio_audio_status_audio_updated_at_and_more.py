# Generated by Django 4.1.7 on 2023-03-23 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0014_audio_conflict_resolved_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='audio',
            name='audio_status',
            field=models.TextField(choices=[('in_review', 'in_review'), ('accepted', 'accepted'), ('rejected', 'rejected'), ('pending', 'pending')], db_index=True, default='pending'),
        ),
        migrations.AddField(
            model_name='audio',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='audio',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='audio',
            name='locale',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='audio',
            name='rejected',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
