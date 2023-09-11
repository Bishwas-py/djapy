```python
from djapy.views.generics import DjapyView
from djapy.mixins.csrf import CSRFExempt
from djapy.mixins.permissions import LoginRequiredMixin
from djapy.pagination.paginator import NumberPaginator
from moco.models import Blog


class ExampleAPIView2(DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model


class ExampleAPIView3(DjapyView, NumberPaginator):
    model_fields = '__all__'
    paginate_by = 10

    def get_queryset(self, request):
        model = Blog.objects.all()
        return model


class ExampleAPIView(CSRFExempt, DjapyView):
    def get(self, request):
        return {
            'name': 'Djapy on GET'
        }

    def post(self, request):
        return {
            'name': 'Djapy on POST'
        }


class ProtectedAPIView(LoginRequiredMixin, DjapyView):
    model_fields = '__all__'

    def get_queryset(self, request):
        model = Blog.objects.get_queryset()
        return model

```