from django.db import models
from accounts.models import User
from setup.models import AppConfiguration


#yapf: disable
class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Image(models.Model):
    name = models.CharField(max_length=255)
    categories = models.ManyToManyField(Category, blank=True, related_name='images')
    source_url = models.URLField(blank=True, null=True)
    file = models.ImageField(upload_to='images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_downloaded = models.BooleanField(default=False)
    validation_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs) -> None:
        self.validation_count = self.validations.count()
        return super().save(*args, **kwargs)

    def validate(self, user, status, category_names):
        required_image_validation_count = AppConfiguration.objects.first().required_image_validation_count
        max_categories_for_image = AppConfiguration.objects.first().max_category_for_image

        categories = self.categories.union(Category.objects.filter(name__in=category_names))[:max_categories_for_image]
        self.categories.set(categories)

        validation,_  = ImageValidation.objects.get_or_create(image=self, user=user)
        validation.is_valid=status=="accepted"
        validation.save()

        self.is_accepted = self.validations.filter(is_valid=True).count() >= required_image_validation_count and len(categories) > 0

        self.save()


class ImageValidation(models.Model):
    image = models.ForeignKey(Image, related_name="validations", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="image_validations", on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.image.name} - {self.is_valid}'