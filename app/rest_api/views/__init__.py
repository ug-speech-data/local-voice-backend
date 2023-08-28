import time
from io import BytesIO

import requests
from django.core import files
from django.core.files.base import ContentFile
from PIL import Image as PillowImage
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
            thumbnail.thumbnail((200, 200), PillowImage.ANTIALIAS)
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

            total_images = Image.objects.filter(deleted=False).count()
            return Response(
                {
                    "message": "success",
                    "total_images": total_images
                },
                status=200)

        except Exception as e:
            print(e)
        return Response({"message": "error"}, status=400)


class AddImageToDatabase(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        file = request.data.get("file")
        category_name = request.data.get("category_name")
        name = request.data.get("name")
        source = request.data.get("source")

        category = Category.objects.filter(name=category_name).first()
        image = None
        try:
            image = Image.objects.create(
                name=name,
                file=file,
                main_category=category,
                is_accepted=True,
                is_downloaded=True,
                source_url=source,
            )
            if category:
                image.categories.add(category)
        except Exception as e:
            logger.error(str(e))
            return Response({"error": str(e)})

        if image:
            image.create_image_thumbnail()

        return Response({"message": "success"}, status=200)
