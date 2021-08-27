import route


# In this example, the string specified by the text parameter will be repeated the specified number of times.


@route.http("GET", args=(
    route.Argument("text", "str", "path", maximum=32),
    route.Argument("count", "int", "path", minimum=1, maximum=100)),
            require_auth=False)
def on_get(handler, params):
    q = params["text"] * params["count"]
    route.success(handler, 200, q)


def params():
    return [
        {
            "name": "text",
            "in": "path",
            "about": "Input text.",
            "required": True,
            "type": "string"
        },
        {
            "name": "count",
            "in": "path",
            "about": "Count.",
            "required": True,
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        }
    ]


def docs():
    return {
        "get": {
            "about": "Outputs the specified text.",
            "returns": "application/json",
            200: {
                "about": "Successful response.",
                "example": {
                    "success": True,
                    "result": "Hello, world!"
                }
            }
        }
    }