from abc import abstractmethod, ABC
from types import NoneType

from django.http import JsonResponse, HttpResponse

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
    request = None
    model_fields = None
    exclude_null_fields: bool = False

    def __init__(self):
        if self.model_fields:
            check_model_fields(self.model_fields)

    def get_queryset(self, request):
        pass

    def __jsonify__(self, queryset):
        return DjapyModelJsonMapper(queryset, self.model_fields,
                                    exclude_null_fields=self.exclude_null_fields).result_data()

    def get_data(self, request):
        pass

    def render(self, request):
        """
        Other classes and mixins can override this render method for additional functionalities
        """

        has_super_render = hasattr(super(), 'render')
        if has_super_render:
            super_render = getattr(super(), 'render')
            return super_render(request)

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
            response = response_func(request)

            if type(response) is NoneType:
                raise Exception(f'Response is None, please check your def {request.method.lower()}() method.')

            if isinstance(response, dict):
                return JsonResponse(response, safe=False)

            if not isinstance(response, HttpResponse):
                raise Exception(f'Cannot convert to JSON: {response}. '
                                f'Please check your def {request.method.lower()}() method.')

        response_data = self.get_data(request)
        if response_data:
            return JsonResponse(response_data, safe=False)

        queryset = self.get_queryset(request)
        if not queryset:
            raise Exception('The get_queryset() method is returning None')

        return JsonResponse(self.__jsonify__(queryset))

    def __render__(self, request):
        self.request = request
        return self.render(request)
