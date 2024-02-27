default_auth = [
    {
        "SessionAuth": [],
        "CSRFTokenAuth": []
    }
]

default_auth_schema = {
    "SessionAuth": {
        "type": "apiKey",
        "in": "cookie",
        "name": "sessionid"
    },
    "CSRFTokenAuth": {
        "type": "apiKey",
        "in": "cookie",
        "name": "csrftoken"
    }
}
