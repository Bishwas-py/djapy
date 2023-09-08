import json
from abc import ABC, abstractmethod
from typing import Optional

from django.http import HttpResponse, JsonResponse

from djapy.views.generics import DjapyBaseView
from djapy.utils.response_format import create_response


class PermissionMixin(DjapyBaseView, ABC):
    @abstractmethod
    def has_permission(self, request) -> bool:
        pass

    @abstractmethod
    def get_error_response(self, request):
        pass

    def __render__(self, request) -> HttpResponse:
        if not self.has_permission(request):
            error_response = self.get_error_response(request)
            return error_response

        return super().__render__(request)


class LoginRequiredMixin(PermissionMixin):
    """
    Please keep "LoginRequiredMixin" before your DjapyView.
    """

    login_required_status: str = 'failed'
    login_required_alias: str = 'login_required'
    login_required_message: str = 'Login is required to perform this action'
    login_required_data: Optional[str] = None
    login_required_extra: Optional[str] = None

    def has_permission(self, request) -> bool:
        return request.user.is_authenticated

    def get_login_required_status(self, request):
        return self.login_required_status

    def get_login_required_alias(self, request):
        return self.login_required_alias

    def get_login_required_message(self, request):
        return self.login_required_message

    def get_login_required_data(self, request):
        return self.login_required_data

    def get_login_required_extra(self, request):
        return self.login_required_extra

    def get_error_response(self, request) -> HttpResponse:
        error_response = create_response(
            self.get_login_required_status(request),
            self.get_login_required_alias(request),
            self.get_login_required_message(request),
            self.get_login_required_data(request),
            self.get_login_required_extra(request)
        )

        return JsonResponse(error_response)
