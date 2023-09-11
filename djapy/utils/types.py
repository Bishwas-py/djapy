from typing import TypedDict, Unpack


class JsonNodeParamsPacked(TypedDict):
    exclude_null_fields: bool


class NodeToModelParamsPacked(TypedDict):
    model_fields: list | str
    node_bounded_mode: str


JsonNodeParams = Unpack[JsonNodeParamsPacked]
NodeToModelParams = Unpack[NodeToModelParamsPacked]
FieldParserType = dict[str, callable] | dict[str, tuple[callable, list | tuple | dict]] | None
