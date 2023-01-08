from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group

#yapf: disable

# General system config table - only one row.
class AppConfiguration(models.Model):
    DEFAULT_API_KEY = settings.ARKESEL_API or ""
    demo_video = models.FileField(upload_to='demovideo/', null=True, blank=True)
    sms_sender_id = models.CharField(max_length=11, unique=True, default="LOCALVOICE")
    api_key = models.CharField(max_length=50, unique=True, default=DEFAULT_API_KEY)
    send_sms = models.BooleanField(default=True)
    max_background_noise_level = models.IntegerField(default=100)
    max_category_for_image = models.IntegerField(default=5)
    required_image_validation_count = models.IntegerField(default=3)
    required_audio_validation_count = models.IntegerField(default=3)
    required_transcription_validation_count = models.IntegerField(default=3)
    required_image_description_count = models.IntegerField(default=3)
    number_of_batches = models.IntegerField(default=10)
    enumerators_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    android_apk = models.FileField(upload_to="apks/", null=True, blank=True)

# Just for permissions
class SetupPerms(models.Model):

    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model.
        default_permissions = ()  # disable "add", "change", "delete"
        # and "view" default permissions
        permissions = [
            ('manage_setup', 'Can manage system setup'),
            ("validate_image", "Can validate image"),
            ("validate_audio", "Can validate audio"),
            ("transcribe_audio", "Can transcribe audio"),
            ("validate_transcription", "Can validate transcription"),
            ("manage_collected_data", "Can manage collected data"),
        ]
