from djapy.schema import Schema


def make_openapi_response(schema_or_dict: Schema | Dict[int, Schema]):
    if isinstance(schema_or_dict, dict):
        responses = {}
        for status, schema in schema_or_dict.items():
            responses[str(status)] = {
                "description": "OK" if status == 200 else "Error",
                "content": {
                    "application/json": {
                        "schema": schema.model_json_schema() if issubclass(schema, Schema) else schema
                    }
                }
            }
        return responses
    return {
        "200": {
            "description": "OK",
            "content": {
                "application/json": {
                    "schema": schema_or_dict.model_json_schema() if issubclass(schema_or_dict,
                                                                               Schema) else schema_or_dict
                }
            }
        }
    }
