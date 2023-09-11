# Views examples

## Simple response from model
```python

from django.http import HttpResponse

from djapy.mixins.permissions import LoginRequiredMixin
from djapy.views.generics import DjapyView
from moco.models import Blog


class ExampleAPIView(DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model
    
class YoYoAPIView(DjapyView):
    model_fields = '__all__'

    def get(self, request):
        return HttpResponse('This is a GET request')
    
    def post(self, request):
        return HttpResponse('This is a POST request')
        



class ProtectedAPIView(LoginRequiredMixin, DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model

```