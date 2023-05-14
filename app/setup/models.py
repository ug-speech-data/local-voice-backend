from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models

#yapf: disable

# General system config table - only one row.
class AppConfiguration(models.Model):
    demo_video_ewe = models.FileField(upload_to="demovideos",null=True, blank=True)
    demo_video_akan = models.FileField(upload_to="demovideos",null=True, blank=True)
    demo_video_dagaare = models.FileField(upload_to="demovideos",null=True, blank=True)
    demo_video_ikposo = models.FileField(upload_to="demovideos",null=True, blank=True)
    demo_video_dagbani = models.FileField(upload_to="demovideos",null=True, blank=True)
    max_background_noise_level = models.IntegerField(default=100)
    max_category_for_image = models.IntegerField(default=5)
    required_image_validation_count = models.IntegerField(default=3)
    required_audio_validation_count = models.IntegerField(default=3)
    required_transcription_validation_count = models.IntegerField(default=3)
    required_image_description_count = models.IntegerField(default=3)
    number_of_batches = models.IntegerField(default=10)
    enumerators_group = models.OneToOneField(Group, related_name="setup_enumerator_group", on_delete=models.CASCADE, null=True, blank=True)
    validators_group = models.OneToOneField(Group, related_name="setup_validator_group", on_delete=models.CASCADE, null=True, blank=True)
    default_user_group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)
    android_apk = models.FileField(upload_to="apks/", null=True, blank=True)
    participant_privacy_statement = models.TextField(default="",null=True, blank=True)
    max_image_for_validation_per_user = models.IntegerField(default=300)
    max_audio_validation_per_user = models.IntegerField(default=50*120*2)

    # Compensation
    participant_amount_per_audio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    amount_per_audio_transcription = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    amount_per_audio_validation = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    audio_aggregators_amount_per_audio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    individual_audio_aggregators_amount_per_audio = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    participant_privacy_statement_audio_ewe = models.FileField(upload_to="privacy_statement_audios",null=True, blank=True)
    participant_privacy_statement_audio_akan = models.FileField(upload_to="privacy_statement_audios",null=True, blank=True)
    participant_privacy_statement_audio_dagaare = models.FileField(upload_to="privacy_statement_audios",null=True, blank=True)
    participant_privacy_statement_audio_ikposo = models.FileField(upload_to="privacy_statement_audios",null=True, blank=True)
    participant_privacy_statement_audio_dagbani = models.FileField(upload_to="privacy_statement_audios",null=True, blank=True)

    allow_saving_less_than_required_per_participant = models.BooleanField(default=False)
    allow_recording_more_than_required_per_participant = models.BooleanField(default=False)
    number_of_audios_per_participant = models.IntegerField(default=120)
    hours_to_keep_audios_for_validation = models.IntegerField(default=12)
    hours_to_keep_audios_for_transcription = models.IntegerField(default=12)

    current_apk_versions = models.CharField(max_length=11,default="")
    limited_groups = models.ManyToManyField(Group, related_name="configurations")

    def save(self, *args, **kwargs) -> None:
        if self.android_apk:
            version = self.android_apk.file.name.split("v")[-1].split("-")[0]
            self.current_apk_versions  = version
            return super().save(*args, **kwargs)



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
            ("resolve_transcription", "Can resolve transcription"),
            ("manage_collected_data", "Can manage collected data"),
            ("manage_payment", "Can manage payments"),
            ("record_self", "Can record oneself"),
            ("record_others", "Can record others"),
            ("approve_sample_audio_recorders", "Can approve sample audio recorders"),
        ]
