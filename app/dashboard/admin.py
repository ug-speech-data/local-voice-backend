from django.contrib import admin

from .models import Category, Image, ImageValidation

admin.site.register(Category)
admin.site.register(Image)
admin.site.register(ImageValidation)

