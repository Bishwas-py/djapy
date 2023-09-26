from django.contrib.auth.models import User
from django.db import models


def is_owned_by(model_object: models.Model, user: User, field_name='user'):
    """
    Checks if the user is the owner of the object. If the mentioned field does not exist, the function will return
    False.
    :param user: The user to check.
    :param model_object: The object to check.
    :param field_name: The name of the field that contains the user.
    """
    if hasattr(model_object, field_name):
        return getattr(model_object, field_name) == user
    return False


def is_allow_in_many_to_many(model_object: models.Model, user: User, field_name='users'):
    """
    Checks if the user is allowed in the many-to-many field of the object. If the mentioned field does not exist, the
    function will return False.
    :param user: The user to check.
    :param model_object: The object to check.
    :param field_name: The name of the field that contains the user.
    """

    if hasattr(model_object, field_name):
        return user in getattr(model_object, field_name).all()
    return False
