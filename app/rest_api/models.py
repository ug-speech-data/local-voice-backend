from django.db import models


class MobileAppConfiguration(models.Model):
    demo_video = models.FileField(upload_to='demovideo/',
                                  null=True,
                                  blank=True)
