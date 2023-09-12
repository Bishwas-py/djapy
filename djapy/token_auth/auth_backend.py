from ..auth.backends import BaseAuthentication
from ..exceptions import AuthBackendException
from .models import AuthToken


class TokenAuth(BaseAuthentication):
    def authenticate(self, request):
        authorization_token = request.headers.get('Authorization')
        if not authorization_token:
            return

        authorization_token = authorization_token.replace('Token', '').strip()

        try:
            auth_token = AuthToken.objects.get(key__exact=authorization_token)
            return auth_token.user
        except AuthToken.DoesNotExist:
            raise AuthBackendException('Invalid auth token')

