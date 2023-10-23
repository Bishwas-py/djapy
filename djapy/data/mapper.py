from types import UnionType, NoneType

from django.http import QueryDict

from djapy.data.fields import get_request_value
from djapy.utils.response_format import create_json


class DataItemsProcess:
    name: str
    source_obj: QueryDict | dict

    def __init__(self, name: str, source_obj: QueryDict | dict):
        self.source_obj = source_obj
        self.name = name

    def perform_items_process(self, items, new_object: object, errors: dict):
        for item_name, item_type in items:
            item_value = get_request_value(self.source_obj, item_name, item_type)
            is_item_default_value_mentioned = hasattr(new_object, item_name)
            is_item_type_union = isinstance(item_type, UnionType)
            is_any_union_none_type = is_item_type_union and any(
                [issubclass(q, NoneType) for q in item_type.__args__])

            is_optional_item = (
                    is_any_union_none_type or
                    is_item_default_value_mentioned
                    or item_type is None
            )

            if not is_optional_item and not item_value:
                errors[item_name] = create_json(
                    'failed', f'{self.name}_not_found',
                    f'{self.name.capitalize()} `{item_name}` is required',
                    field_name=item_name,
                    field_type=self.name
                )
            else:
                if not item_value:
                    item_value = getattr(new_object, item_name, None)
                setattr(new_object, item_name, item_value)


class DataWrapper:
    x_data: dict

    def __init__(self):
        self.x_data = {}

    def add_data(self, key, value):
        self.x_data[key] = value

    def get_data(self, key):
        return self.x_data.get(key, None)

    def __getattr__(self, attr):
        if attr in self.x_data:
            return self.x_data[attr]
        raise AttributeError(f"'DataWrapper' object has no attribute '{attr}'")


class QueryWrapper:
    x_query: dict

    def __init__(self):
        self.x_query = {}

    def add_query(self, key, value):
        self.x_query[key] = value

    def get_query(self, key):
        return self.x_query.get(key, None)

    def __getattr__(self, attr):
        if attr in self.x_query:
            return self.x_query[attr]
        raise AttributeError(f"'QueryWrapper' object has no attribute '{attr}'")

    def __getitem__(self, item):
        return self.x_query[item]

    def get(self, item, default=None):
        return self.x_query.get(item, default)
