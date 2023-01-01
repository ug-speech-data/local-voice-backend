from django.contrib import admin

from .models import Category, Image, Participant, Audio, Validation

admin.site.register(Category)
admin.site.register(Image)
admin.site.register(Participant)
admin.site.register(Audio)
admin.site.register(Validation)
