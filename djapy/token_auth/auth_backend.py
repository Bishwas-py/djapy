from django.contrib.auth import login, logout

from .models import AuthToken
from ..exceptions import AuthBackendException


class TokenAuth:
    def authenticate(self, request):
        authorization_token = request.headers.get('Authorization')
        if not authorization_token:
            logout(request)
            return

        authorization_token = authorization_token.replace('Token', '').strip()

        try:
            auth_token = AuthToken.objects.get(key__exact=authorization_token)
        except AuthToken.DoesNotExist:
            raise AuthBackendException('Invalid auth token')

        login(request, auth_token.user)
