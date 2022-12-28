from rest_framework import generics
from rest_framework.response import Response

from local_voice.utils.functions import get_errors_from_form


class SimpleCrudMixin(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        categories = self.model_class.objects.all()
        response_data = {
            self.response_data_label_plural:
            self.serializer_class(categories, many=True).data,
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
        return Response(
            {"error_message": f"{self.model_class.__name__} could not be deleted"})
