import json
from typing import Dict, Any, List

from pydantic import ValidationError
from pydantic_core import InitErrorDetails


def create_json_from_validation_error(exception: ValidationError, detailed: bool = True) -> Dict[str, Any]:
   """Create a structured error response from Pydantic ValidationError.
   
   Args:
       exception: The Pydantic ValidationError
       detailed: If True, include full error details; if False, simplified version
   
   Returns:
       Structured error dictionary compatible with OpenAPI
   """
   errors = exception.errors()
   
   if detailed:
      return {
         'errors': errors,
         'error_count': exception.error_count(),
         'title': str(exception.title),
         'type': 'validation_error'
      }
   
   # Simplified error format
   formatted_errors = []
   for error in errors:
      loc = ' -> '.join(str(x) for x in error['loc'])
      formatted_errors.append({
         'field': loc,
         'message': error['msg'],
         'type': error['type']
      })
   
   return {
      'errors': formatted_errors,
      'error_count': len(formatted_errors),
      'type': 'validation_error'
   }


def create_validation_error(title: str, loc_name: str, _type: str, msg: str = None) -> ValidationError:
   """Create a custom ValidationError with better error messages.
   
   Args:
       title: Error title
       loc_name: Location/field name
       _type: Error type
       msg: Optional custom error message
   
   Returns:
       ValidationError instance
   """
   error_details = InitErrorDetails(
      loc=(loc_name,),
      type=_type,
      input=None,
   )
   
   if msg:
      error_details = InitErrorDetails(
         loc=(loc_name,),
         type=_type,
         input=None,
         msg=msg
      )
   
   return ValidationError.from_exception_data(
      title=title,
      line_errors=[error_details],
      input_type="python",
   )


def format_error_response(error_type: str, message: str, details: Any = None, status_code: int = 400) -> Dict[str, Any]:
   """Create a standardized error response format.
   
   Args:
       error_type: Type of error (e.g., 'validation_error', 'authentication_error')
       message: Human-readable error message
       details: Additional error details
       status_code: HTTP status code
   
   Returns:
       Standardized error dictionary
   """
   response = {
      'type': error_type,
      'message': message,
      'status': status_code
   }
   
   if details:
      response['details'] = details
   
   return response
