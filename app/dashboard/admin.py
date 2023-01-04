from django.contrib import admin

from .models import Category, Image, Participant, Audio, Validation, Transaction

admin.site.register(Category)
admin.site.register(Image)
admin.site.register(Participant)
admin.site.register(Audio)
admin.site.register(Validation)
admin.site.register(Transaction)
