from pydantic import ValidationError


def create_json_from_validation_error(exception: ValidationError):
    return {
        'error': exception.errors(),
        'error_count': exception.error_count(),
        'title': exception.title
    }
