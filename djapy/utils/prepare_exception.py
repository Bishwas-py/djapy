import logging
import traceback


def log_exception(request, exception):
    error_uri = request.build_absolute_uri()
    error = repr(exception)
    tb = traceback.format_exc()
    error_message = f"{error_uri}\n{error}\n{tb}"
    logging.error(error_message)
    display_message = f"An error occurred on `{error_uri}`, have a look at the logs for more details."
    first_function = traceback.extract_tb(exception.__traceback__)
    print(first_function)
    return error, display_message
