import uuid

from django.contrib.auth import get_user_model
from django.db import models


class AuthToken(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    key = models.CharField(max_length=100, blank=True, help_text='Leave empty to autogenerate')

    def save(self, *args, **kwargs):
        if not self.pk:
            key = str(uuid.uuid4())
            self.key = key.replace('-', '')

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.user)
