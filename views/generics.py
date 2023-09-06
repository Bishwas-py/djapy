from abc import abstractmethod, ABC

from django.views import View
from django.http import HttpResponse
from django.utils.decorators import classonlymethod
from django.views import View

from djapy import JsonNode


class APIView(ABC):
    model_fields = None
    node_bounded_mode: str = "__strict__"

    def __init__(self):
        if not self.model_fields:
            raise Exception('Please specify model fields')

    def __render__(self, request):
        queryset = self.get_queryset(request)
        json_node = JsonNode(queryset, self.model_fields, node_bounded_mode=self.node_bounded_mode)
        return json_node.nodify()

    @abstractmethod
    def get_queryset(self, request):
        pass

    @classmethod
    def as_view(cls):
        view = cls()
        return view.__render__
