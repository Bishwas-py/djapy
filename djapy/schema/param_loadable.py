__all__ = ['is_payload_type', 'as_json', 'as_form']

from typing import Generic, Literal, Any

from djapy.core.typing_utils import G_TYPE


class Cvar:
   form = "application/x-www-form-urlencoded"
   json = "application/json"


CvarLiteral = Literal["application/x-www-form-urlencoded", "application/json"]


def _payload_instance(cls, un, cvar_c_type: CvarLiteral):
   instance = cls()
   instance.unquery_type = un
   instance.cvar_c_type = cvar_c_type
   return instance


class AsJson(Generic[G_TYPE]):
   def __class_getitem__(cls, un: G_TYPE) -> G_TYPE:
      return _payload_instance(cls, un, Cvar.json)


class AsForm(Generic[G_TYPE]):
   def __class_getitem__(cls, un: G_TYPE) -> G_TYPE:
      return _payload_instance(cls, un, Cvar.form)


as_json = AsJson
as_form = AsForm

LoadParam = AsJson | AsForm | None


def is_payload_type(load_param: Any | LoadParam) -> LoadParam:
   """
   Determine if the parameter is a payload type.

   :param load_param: The parameter to analyze
   :return: The payload type or None
   """
   if load_param and hasattr(load_param, 'unquery_type') and isinstance(load_param, (AsJson, AsForm)):
      return load_param
   return None
