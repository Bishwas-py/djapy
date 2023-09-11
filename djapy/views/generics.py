from abc import abstractmethod, ABC

from djapy.parser.models_parser import check_model_fields
from djapy.utils.mapper import DjapyModelJsonMapper


class DjapyBaseView(ABC):

    @abstractmethod
    def __render__(self, request):
        pass

    @classmethod
    def as_view(cls):
        view = cls()
        return view.__render__


class DjapyView(DjapyBaseView, ABC):
    model_fields = None
    node_bounded_mode: str = "__strict__"

    def __init__(self):
        check_model_fields(self.model_fields)

    def get_queryset(self, request):
        pass

    def render(self, request):
        queryset = self.get_queryset(request)
        if not queryset:
            raise Exception('The get_queryset() method is returning None')

        json_node = DjapyModelJsonMapper(queryset, self.model_fields, node_bounded_mode=self.node_bounded_mode)
        return json_node.nodify()

    def __render__(self, request):
        """
        Check if the developer has declared a custom response based on request method.
        For example:

        def get(self, request):
            pass

        def post(self, request):
            pass
        """

        response_based_on_request_method_declared = hasattr(self, request.method.lower())
        if response_based_on_request_method_declared:
            response_func = getattr(self, request.method.lower())
            return response_func(request)

        return self.render(request)
