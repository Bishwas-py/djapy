from typing import TypedDict, Unpack


class JsonNodeParamsPacked(TypedDict):
    excluded_error: str
    only_included_error: str
    node_bounded_mode: str


JsonNodeParams = Unpack[JsonNodeParamsPacked]
