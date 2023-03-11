from datetime import datetime
from functools import reduce
from io import BytesIO

import requests
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from PIL import Image as PillowImage
from PIL import UnidentifiedImageError

from accounts.models import User
from local_voice.utils.constants import TransactionDirection
from payments.models import Transaction
from setup.models import AppConfiguration


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "notifications"

    def __str__(self):
        return self.title


# yapf: disable
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Validation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "validations"

    def __str__(self):
        return f'{self.user} - {self.is_valid}'


class Image(models.Model):
    name = models.CharField(max_length=255)
    main_category = models.ForeignKey(Category, related_name="main_images", on_delete=models.SET_NULL, null=True, blank=True)
    categories = models.ManyToManyField(
        Category, blank=True, related_name='images')
    source_url = models.URLField(blank=True, null=True, unique=True)
    file = models.ImageField(upload_to='images/', blank=True, null=True)
    is_accepted = models.BooleanField(default=False, db_index=True)
    is_downloaded = models.BooleanField(default=False)
    validation_count = models.IntegerField(default=0)
    validated = models.BooleanField(default=False)
    thumbnail = models.ImageField(
        upload_to='thumbnails/', blank=True, null=True)
    validations = models.ManyToManyField(
        Validation, related_name='image_validations', blank=True)
    batch_number = models.IntegerField(
        default=-1, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "images"

    def __str__(self):
        return self.name

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query})
                   for key in ["name", "categories__name"]]
        return reduce(lambda x, y: x | y, queries)

    def save(self, *args, **kwargs) -> None:
        normal_save = kwargs.pop("normal_save",None)
        if not normal_save:
            if self.pk is not None:
                self.validation_count = self.validations.all().count()

            if self.validation_count > 0:
                self.validated = True
        return super().save(*args, **kwargs)

    def format_image_name(self):
        cat_name = self.main_category.name.split()[0].replace(",", "").lower() + "_" if self.main_category else "1"
        new_filename = cat_name + f"{self.id}".zfill(6) + ".jpg"
        image = PillowImage.open(self.file)
        temp_io = BytesIO()
        image = image.convert("RGB")
        image.save(temp_io, "jpeg")
        self.file = File(temp_io,new_filename)
        self.name = new_filename

        # Rename thumbnail
        new_filename = "2" + f"{self.id}".zfill(9) + ".jpg"
        image = PillowImage.open(self.thumbnail)
        temp_io = BytesIO()
        image = image.convert("RGB")
        image.save(temp_io, "jpeg")
        self.thumbnail = File(temp_io,new_filename)
        self.save()

    def validate(self, user, status, category_names):
        required_image_validation_count = AppConfiguration.objects.first(
        ).required_image_validation_count
        max_categories_for_image = AppConfiguration.objects.first().max_category_for_image

        categories = self.categories.union(Category.objects.filter(
            name__in=category_names))[:max_categories_for_image]
        self.categories.set(categories)

        validation = Validation.objects.filter(
            user=user, image_validations=self).first()
        if validation is None:
            validation = Validation.objects.create(user=user)
        validation.is_valid = status == "accepted"
        self.validations.add(validation)
        validation.save()
        self.save()

        is_accepted = self.validation_count >= required_image_validation_count and self.validation_count == self.validations.filter(
            is_valid=True).count() and len(categories) > 0
        self.is_accepted = is_accepted

        if is_accepted:
            self.main_category = Category.objects.filter(name=category_names[0]).first()
        else:
            self.main_category = None
        self.save()

    def create_image_thumbnail(self, height=200, width=200):
        thumbnail = PillowImage.open(self.file)
        thumbnail.thumbnail((height, width), PillowImage.ANTIALIAS)
        thumb_io = BytesIO()
        thumbnail = thumbnail.convert('RGB')
        thumbnail.save(thumb_io, "jpeg", quality=80)
        self.thumbnail = File(
            thumb_io, name=self.name.split(".")[0] + ".jpg")
        self.save(normal_save=True)

    def download(self):
        if self.is_downloaded:
            return

        response = requests.get(self.source_url)
        if response.status_code != requests.codes.ok:
            return

        try:
            image = PillowImage.open(BytesIO(response.content))
            width, height = image.size
            if width >= 400 and height >= 400:
                self.file.save(self.name, ContentFile(response.content))

                # Create thumbnail
                thumbnail = PillowImage.open(BytesIO(response.content))
                thumbnail.thumbnail((200, 200), PillowImage.ANTIALIAS)
                thumb_io = BytesIO()
                thumbnail = thumbnail.convert('RGB')
                thumbnail.save(thumb_io, "jpeg", quality=50)
                self.thumbnail = File(
                    thumb_io, name=self.name.split(".")[0] + ".jpg")

                self.is_downloaded = True
                self.save()
        except (UnidentifiedImageError) as e:
            print(e)


class Participant(models.Model):
    momo_number = models.CharField(
        max_length=255, db_index=True, blank=True, null=True)
    network = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    fullname = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True)
    submitted_by = models.ForeignKey(
        User, related_name="participant", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    audio_duration_in_seconds = models.IntegerField(default=0)
    paid = models.BooleanField(default=False, db_index=True)
    transaction = models.OneToOneField(
        Transaction, related_name="participant", on_delete=models.SET_NULL, blank=True, null=True)
    accepted_privacy_policy = models.BooleanField(default=False)
    api_client = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "participants"

    def pay_participant(self, user):
        if self.paid:
            return

        transaction = Transaction.objects.filter(participant=self).first()
        if not transaction:
            transaction = Transaction.objects.create()
        transaction.amount = self.amount
        transaction.phone_number = self.momo_number
        transaction.network = self.network
        transaction.status = "new"
        transaction.fullname = self.fullname
        transaction.note = "PARTICIPANT_PAYMENT"
        transaction.initiated_by = user
        transaction.direction = TransactionDirection.OUT.value
        transaction.save()
        self.transaction = transaction
        self.save()

        # Make API calls
        transaction.execute()

    def check_payment_status(self):
        if self.transaction:
            if self.transaction.success():
                self.paid = True
                self.save()
            else:
                self.transaction.recheck_status()

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query})
                   for key in ["momo_number", "fullname", "gender"]]
        return reduce(lambda x, y: x | y, queries)

    def save(self, *args, **kwargs):
        if self.pk is None and self.fullname is not None:
            slug = "-".join(sorted(self.fullname.split()))
            self.slug = slug
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


class Audio(models.Model):
    image = models.ForeignKey(Image, db_index=True,
                              related_name="audios", on_delete=models.CASCADE)
    file = models.FileField(upload_to='audios/')
    submitted_by = models.ForeignKey(
        User, related_name="audios", on_delete=models.CASCADE)
    participant = models.ForeignKey(
        Participant, related_name="audios", on_delete=models.SET_NULL, null=True, blank=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    validation_count = models.IntegerField(default=0, db_index=True)
    transcription_count = models.IntegerField(default=0)
    year = models.IntegerField(blank=True, default=2023, null=True)
    locale = models.CharField(max_length=255, blank=True, null=True)
    api_client = models.CharField(max_length=255, blank=True, null=True)
    duration = models.IntegerField(default=-1, blank=True, null=True)
    environment = models.CharField(max_length=255, blank=True, null=True)
    is_accepted = models.BooleanField(default=False, db_index=True)
    validations = models.ManyToManyField(
        Validation, related_name='audio_validations', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audios"

    def __str__(self):
        return f'{self.image.name} - {self.submitted_by}'

    def save(self, *args, **kwargs) -> None:
        if self.pk is not None:
            self.validation_count = self.validations.all().count()
            self.transcription_count = self.transcriptions.filter().count()
            self.year = datetime.now().year
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query}) for key in ["environment", "locale",
                                                                 "device_id", "submitted_by__email_address", "year", "image__name"]]
        return reduce(lambda x, y: x | y, queries)

    def validate(self, user, status):
        required_audio_validation_count = AppConfiguration.objects.first(
        ).required_audio_validation_count

        validation = Validation.objects.filter(
            user=user, audio_validations=self).first()
        if validation is None:
            validation = Validation.objects.create(user=user)
        validation.is_valid = status == "accepted"
        self.validations.add(validation)
        validation.save()
        self.save()

        is_accepted = self.validation_count >= required_audio_validation_count and self.validations.filter(
            is_valid=True).count() == self.validation_count
        self.is_accepted = is_accepted

        self.save()

    def get_transcriptions(self):
        if not hasattr(self, "transcriptions"):
            return []
        values = []
        for t in self.transcriptions.all().values("text"):
            values.append(t.get("text"))
        return values


class Transcription(models.Model):
    audio = models.ForeignKey(
        Audio, db_index=True, related_name="transcriptions", on_delete=models.CASCADE)
    text = models.TextField()
    user = models.ForeignKey(
        User, db_index=True, related_name="transcriptions", on_delete=models.CASCADE)
    validations = models.ManyToManyField(
        Validation, related_name='transcription_validations', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False, db_index=True)
    validation_count = models.IntegerField(default=0, db_index=True)

    class Meta:
        db_table = "transcriptions"

    @staticmethod
    def generate_query(query):
        queries = [Q(**{f"{key}__icontains": query})
                   for key in ["audio__environment", "user__email_address", "audio__locale"]]
        return reduce(lambda x, y: x | y, queries)

    def save(self, *args, **kwargs) -> None:
        if self.pk is not None:
            self.validation_count = self.validations.all().count()
        return super().save(*args, **kwargs)

    def validate(self, user, status):
        required_transcription_validation_count = AppConfiguration.objects.first(
        ).required_transcription_validation_count

        validation = Validation.objects.filter(
            user=user, transcription_validations=self).first()
        if validation is None:
            validation = Validation.objects.create(user=user)
        validation.is_valid = status == "accepted"
        validation.save()
        self.validations.add(validation)
        self.save()

        is_accepted = self.validation_count >= required_transcription_validation_count and self.validations.filter(
            is_valid=True).count() == self.validation_count
        self.is_accepted = is_accepted

        self.save()

    def __str__(self):
        return self.text.split(" ")[50]
