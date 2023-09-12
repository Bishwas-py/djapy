from abc import ABC, abstractmethod


class BaseAuthentication(ABC):
    @abstractmethod
    def authenticate(self, request):
        pass

    def __authenticate__(self, request):
        user = self.authenticate(request)
        if user:
            request.user = user
