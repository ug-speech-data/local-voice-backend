import math
from rest_framework import generics
from rest_framework.response import Response

from local_voice.utils.functions import get_errors_from_form

QUERY_PAGE_SIZE = 50


class SimpleCrudMixin(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        objects = self.model_class.objects.all().order_by("-id")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", QUERY_PAGE_SIZE))

        paginated_objects = objects[(page - 1) * page_size:page * page_size]
        prev_page = page - 1 if page > 1 else None
        total_pages = math.ceil(objects.count() / page_size)
        next_page = page + 1 if total_pages > page else None

        #yapf: disable
        response_data = {
            self.response_data_label_plural:
            self.serializer_class(paginated_objects, many=True).data,
            "page": page,
            "page_size": page_size,
            "total": objects.count(),
            "next_page": next_page,
            "previous_page": prev_page,
            "total_pages": total_pages,
        }
        return Response(response_data)

    def post(self, request, *args, **kwargs):
        obj_id = request.data.get("id")
        obj = None
        if obj_id:
            obj = self.model_class.objects.filter(id=obj_id).first()
        form = self.form_class(request.data, instance=obj)
        if form.is_valid():
            form.save()
            return Response({
                "message":
                f"{self.model_class.__name__} saved successfully",
                self.response_data_label:
                self.serializer_class(form.instance).data,
            })
        return Response({
            "message": f"{self.model_class.__name__} could not be saved",
            "error_message": get_errors_from_form(form),
        })

    def delete(self, request, *args, **kwargs):
        obj_id = request.data.get("id")
        obj = self.model_class.objects.filter(id=obj_id).first()
        if obj:
            try:
                obj.delete()
                return Response({
                    "success_message":
                    f"{self.model_class.__name__} deleted successfully"
                })
            except Exception as e:
                return Response({
                    "error_message":
                    f"{self.model_class.__name__} could not be deleted: {e}"
                })
        return Response({
            "error_message":
            f"{self.model_class.__name__} could not be deleted"
        })
