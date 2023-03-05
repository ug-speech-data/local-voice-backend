import time
from io import BytesIO

import requests
from django.core import files
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError
from PIL import Image as PillowImage
from PIL import UnidentifiedImageError
from rest_framework import generics, permissions
from rest_framework.response import Response

from dashboard.models import Image

from .common import *
from .mobile_app import *
from .web_app import *


class SubmitCrawlerImages(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        source_url = request.data.get("url")
        filename = source_url.split("/")[-1].split("?")[-1]
        filename = str(time.time_ns()) + f".jpg"

        response = requests.get(source_url)
        if response.status_code != requests.codes.ok:
            return Response({"message": "error"}, status=400)

        try:
            image = PillowImage.open(BytesIO(response.content))
            thumbnail = PillowImage.open(BytesIO(response.content))
            thumbnail.thumbnail((100, 100), PillowImage.ANTIALIAS)
            thumb_io = BytesIO()
            thumbnail = thumbnail.convert('RGB')
            thumbnail.save(thumb_io, "jpeg", quality=50)

            width, height = image.size
            if width >= 400 and height >= 400:
                i = Image.objects.create(
                    source_url=source_url,
                    name=filename,
                    is_downloaded=True,
                    thumbnail=files.File(thumb_io, filename),
                    file=files.File(ContentFile(response.content), filename))

            total_images = Image.objects.count()
            return Response(
                {
                    "message": "success",
                    "total_images": total_images
                },
                status=200)

        except (UnidentifiedImageError, IntegrityError) as e:
            print(e)
        return Response({"message": "error"}, status=400)
