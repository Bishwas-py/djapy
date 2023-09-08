from abc import abstractmethod, ABC

from djapy.utils.mapper import DjapyModelJsonMapper, check_model_fields


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

    def __render__(self, request):
        queryset = self.get_queryset(request)
        json_node = DjapyModelJsonMapper(queryset, self.model_fields, node_bounded_mode=self.node_bounded_mode)
        return json_node.nodify()

    @abstractmethod
    def get_queryset(self, request):
        pass
