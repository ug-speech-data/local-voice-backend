from django.db import models


#yapf: disable
class Statistics(models.Model):
    images_submitted = models.IntegerField(default=0)
    images_approved = models.IntegerField(default=0)

    # All Audios
    audios_submitted = models.IntegerField(default=0)
    audios_approved = models.IntegerField(default=0)
    audios_transcribed = models.IntegerField(default=0)

    audios_hours_submitted = models.IntegerField(default=0)
    audios_hours_approved = models.IntegerField(default=0)
    audios_hours_transcribed = models.IntegerField(default=0)

    ########### EWE ########################
    # Total Count
    ewe_audios_submitted = models.IntegerField(default=0)
    ewe_audios_single_validation = models.IntegerField(default=0)
    ewe_audios_double_validation = models.IntegerField(default=0)
    ewe_audios_validation_conflict = models.IntegerField(default=0)
    ewe_audios_approved = models.IntegerField(default=0)
    ewe_audios_transcribed = models.IntegerField(default=0)

    # Total Hours
    ewe_audios_submitted_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ewe_audios_single_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ewe_audios_double_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ewe_audios_validation_conflict_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ewe_audios_approved_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ewe_audios_transcribed_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)


    ########### AKAN ########################
    # Total Count
    akan_audios_submitted = models.IntegerField(default=0)
    akan_audios_single_validation = models.IntegerField(default=0)
    akan_audios_double_validation = models.IntegerField(default=0)
    akan_audios_validation_conflict = models.IntegerField(default=0)
    akan_audios_approved = models.IntegerField(default=0)
    akan_audios_transcribed = models.IntegerField(default=0)

    # Total Hours
    akan_audios_submitted_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    akan_audios_single_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    akan_audios_double_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    akan_audios_validation_conflict_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    akan_audios_approved_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    akan_audios_transcribed_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)


    ########### DAGBANI ########################
    # Total Count
    dagbani_audios_submitted = models.IntegerField(default=0)
    dagbani_audios_single_validation = models.IntegerField(default=0)
    dagbani_audios_double_validation = models.IntegerField(default=0)
    dagbani_audios_validation_conflict = models.IntegerField(default=0)
    dagbani_audios_approved = models.IntegerField(default=0)
    dagbani_audios_transcribed = models.IntegerField(default=0)

    # Total Hours
    dagbani_audios_submitted_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagbani_audios_single_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagbani_audios_double_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagbani_audios_validation_conflict_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagbani_audios_approved_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagbani_audios_transcribed_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)

    ########### DAGAARE ########################
    # Total Count
    dagaare_audios_submitted = models.IntegerField(default=0)
    dagaare_audios_single_validation = models.IntegerField(default=0)
    dagaare_audios_double_validation = models.IntegerField(default=0)
    dagaare_audios_validation_conflict = models.IntegerField(default=0)
    dagaare_audios_approved = models.IntegerField(default=0)
    dagaare_audios_transcribed = models.IntegerField(default=0)

    # Total Hours
    dagaare_audios_submitted_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagaare_audios_single_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagaare_audios_double_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagaare_audios_validation_conflict_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagaare_audios_approved_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    dagaare_audios_transcribed_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)

    ########### IKPOSO ########################
    # Total Count
    ikposo_audios_submitted = models.IntegerField(default=0)
    ikposo_audios_single_validation = models.IntegerField(default=0)
    ikposo_audios_double_validation = models.IntegerField(default=0)
    ikposo_audios_validation_conflict = models.IntegerField(default=0)
    ikposo_audios_approved = models.IntegerField(default=0)
    ikposo_audios_transcribed = models.IntegerField(default=0)

    # Total Hours
    ikposo_audios_submitted_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ikposo_audios_single_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ikposo_audios_double_validation_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ikposo_audios_validation_conflict_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ikposo_audios_approved_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)
    ikposo_audios_transcribed_in_hours = models.DecimalField(default=0.0, decimal_places=4, max_digits=20)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
