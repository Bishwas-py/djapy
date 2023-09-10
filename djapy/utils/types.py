from typing import TypedDict, Unpack


class JsonNodeParamsPacked(TypedDict):
    excluded_error: str
    only_included_error: str
    is_strictly_bounded: str


class NodeToModelParamsPacked(TypedDict):
    model_fields: list | str
    node_bounded_mode: str


JsonNodeParams = Unpack[JsonNodeParamsPacked]
NodeToModelParams = Unpack[NodeToModelParamsPacked]
FieldParserType = dict[str, callable] | dict[str, tuple[callable, list | tuple | dict]] | None
