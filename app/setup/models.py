from django.conf import settings
from django.db import models


# General system config table - only one row.
class SysConfig(models.Model):
    DEFAULT_API_KEY = settings.ARKESEL_API or ""
    sms_sender_id = models.CharField(max_length=11,
                                     unique=True,
                                     default="GHPOLPEN")
    api_key = models.CharField(max_length=50,
                               unique=True,
                               default=DEFAULT_API_KEY)
    send_sms = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


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
