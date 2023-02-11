from django.contrib import admin

from .models import (Audio, Category, Image, Participant, Transaction,
                     Validation)

admin.site.register(Category)
admin.site.register(Image)
admin.site.register(Participant)
admin.site.register(Audio)
admin.site.register(Validation)
admin.site.register(Transaction)
