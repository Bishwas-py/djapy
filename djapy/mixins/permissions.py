from abc import ABC, abstractmethod

from djapy.views.generics import DjapyBaseView
from django.http import HttpResponse


class PermissionMixin(DjapyBaseView, ABC):
    @abstractmethod
    def has_permission(self, request) -> bool:
        pass

    def __render__(self, request) -> HttpResponse:
        if not self.has_permission(request):
            print('no permission')

        return super().__render__(request)


class LoginRequiredMixin(PermissionMixin):
    def has_permission(self, request) -> bool:
        return request.user.is_authenticated
