import json
import os
import pathlib
import re
import uuid

import endpoint
import route
import yaml

_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>%%NAME%%</title>
    <link href=
        "https://fonts.googleapis.com/css?family=Open+Sans:400,700|Source+Code+Pro:300,600|Titillium+Web:400,600,700"
    rel="stylesheet">
    <link rel="stylesheet" type="text/css"
        href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui.css">
    <style>
        html{
            box-sizing:border-box;
            overflow:-moz-scrollbars-vertical;
            overflow-y:scroll;
        }
        [class~=swagger-ui] select,.swagger-ui .scheme-container,[class~=swagger-ui] [class~=info] [class~=title]{
            background-color:#252525;
        }
        *:before,*,*:after{
            box-sizing:inherit;
        }
        [class~=swagger-ui] [class~=opblock] [class~=opblock-section-header] label,
        [class~=swagger-ui] [class~=opblock-description-wrapper] p,[class~=swagger-ui] [class~=parameter__deprecated],
        [class~=swagger-ui],[class~=swagger-ui] [class~=responses-inner] h4,
        [class~=swagger-ui] [class~=opblock-title_normal] p,
        [class~=swagger-ui] [class~=opblock] [class~=opblock-section-header] h4,[class~=swagger-ui] textarea,
        [class~=swagger-ui] [class~=info] [class~=base-url],[class~=swagger-ui] [class~=btn],[class~=swagger-ui] label,
        [class~=swagger-ui] [class~=parameter__name],[class~=swagger-ui] [class~=parameter__type],
        [class~=swagger-ui] [class~=parameter__in],[class~=swagger-ui] [class~=response-col_status],
        .swagger-ui .opblock .opblock-summary-description,[class~=swagger-ui] [class~=info] table,
        [class~=swagger-ui] [class~=info] [class~=title],.swagger-ui .responses-inner h5,
        [class~=swagger-ui] table thead tr th,[class~=swagger-ui] [class~=opblock-external-docs-wrapper] p,
        [class~=swagger-ui] table thead tr td,
        [class~=swagger-ui] [class~=info] [class~=title],body,[class~=swagger-ui] select,.swagger-ui .scheme-container,
        [class~=swagger-ui] [class~=info] p,[class~=swagger-ui] [class~=tab] li,[class~=swagger-ui] [class~=info] li,
        [class~=swagger-ui] a[class~=nostyle],
        .swagger-ui .dialog-ux .modal-ux-header h3,
        .swagger-ui .dialog-ux .modal-ux-content h4,
        .swagger-ui .dialog-ux .modal-ux-content p,
        .swagger-ui .model {
            color:#ccc !important;
        }
        [class~=swagger-ui] [class~=opblock] [class~=opblock-section-header]{
            background-color:transparent;
        }
        body{
            margin-left:0;
            margin-right:0;
            background-color:#252525;
        }

        * {
            font-family: -apple-system,BlinkMacSystemFont,"Segoe UI Variable","Segoe UI",
                system-ui,ui-sans-serif,Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji" !important;
        }

        pre code span {
            font-family: ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace !important;
        }

        ::-webkit-scrollbar {width: 12px; height: 6px;}
        ::-webkit-scrollbar-thumb {-webkit-border-radius: 10px;}
        ::-webkit-scrollbar-track:vertical {-webkit-box-shadow: -1px 0 0 #ededed;}
        ::-webkit-scrollbar-track {background-color: transparent;}
        ::-webkit-scrollbar {width: 12px;}
        ::-webkit-scrollbar-thumb {background-color: rgba(115, 115, 115, 0.2);}
        ::-webkit-scrollbar-thumb { background-color: rgba(166, 166, 166, 0.27); }

        .swagger-ui .opblock {
            background: rgba(97,175,254, .2);
        }

        .swagger-ui .dialog-ux .modal-ux, .swagger-ui .dialog-ux .modal-ux-header {
            background: #252525;
            border-color: #4f4f4f;
            border-width: 2px;
        }

        .swagger-ui .opblock-tag {
            border-color: #aaa;
        }

        svg.arrow,
        .authorization__btn svg {
            fill: #d4dee7;
        }

        input {
            background: #222 !important;
            border-color: #555 !important;
            color: #ccc;
        }

        .swagger-ui .btn.execute {
            color: #fff !important;
        }
    </style>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui-bundle.js"> </script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui-standalone-preset.js"> </script>
<script>
    window.onload = function() {
        window.ui = SwaggerUIBundle({
            spec: "",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ]
        })
    }
</script>
</body>
</html>
"""

_SWAGGER_TEMPLATE = """
swagger: "2.0"
info:
  description: "API Docs"
  title: "API Document"
  version: "latest"
host: "127.0.0.1"
basePath: "/"
schemes:
- http
securityDefinitions:
  token:
    type: "apiKey"
    name: "Authorization"
    in: "header"
security:
  - token: []

"""


def printf(string):
    print(string, end="")


def process_step(target):
    c = 0
    obj = target
    for step in steps:
        c = c + 1
        print(f"\n------------Processing step {step.__name__} of {c}/{len(steps)}------------")
        try:
            obj = step(obj)
        except TypeError:
            obj = step()


global swagger


def whats_type_of_this_object(obj):
    typ3 = type(obj)
    if typ3 is dict or typ3 is tuple:
        return "object"
    elif typ3 is bool:
        return "boolean"
    elif typ3 is str:
        return "string"
    elif typ3 is int:
        return "integer"
    elif typ3 is list:
        return "array"
    return None


def generate_html(obj: dict):
    print("Generating docs html...")
    rz = json.dumps(obj)
    with open("docs.html", "w", encoding="utf-8") as w:
        w.write(_HTML_TEMPLATE.replace("\"\"", rz).replace("%%NAME%%", obj["info"]["title"]))


def save(obj: dict):
    print("Exporting swagger settings...")
    if not os.path.exists("docs/"):
        os.mkdir("docs")
    with open("docs/swagger.yml", "w", encoding="utf-8") as w:
        w.write(yaml.dump(obj))
    return obj


def build_swagger(obj: dict):
    print("Building swagger file...")
    print("Initializing swagger...")
    swagger["paths"] = {}
    for o in obj.items():
        swagger["paths"][o[0]] = o[1]
        print(f"{o[0]} was built successfully.")
    return swagger


def normalize_params(obj: dict):
    for gz in obj.items():
        for method in list(gz[1].items()):
            print(f"Normalizing parameters of '{gz[0]} - {method[0]}'...")
            if "parameters" not in gz[1][method[0]]:
                print(f"No parameters was found in '{gz[0]} - {method[0]}'.")
                continue
            for param in list(gz[1][method[0]]["parameters"]):
                param["description"] = param["about"]
                del param["about"]
                if "required" in param:
                    if param["in"] == "path":
                        param["required"] = True
                elif param["in"] == "path":
                    param["required"] = True
                else:
                    param["required"] = False
    return obj


def b(ex):
    properties = {}
    for zz in ex.items():
        tz = whats_type_of_this_object(zz[1])
        if tz is "array":

            a_t_field = ""
            for at in zz[1]:
                fa = whats_type_of_this_object(at)
                if a_t_field != "" and a_t_field != fa:
                    a_t_field = "object"
                    break
                a_t_field = fa

            if a_t_field == "":
                a_t_field = "object"

            properties[zz[0]] = {
                "type": tz,
                "items": {
                    "type": a_t_field
                }
            }

            if a_t_field == "object":
                i = 0
                properties[zz[0]]["items"]["properties"] = {}
                for hb in zz[1][0].items():
                    ahx = whats_type_of_this_object(hb)
                    bz = {
                        "type": ahx,
                        "example": hb[0]
                    }
                    if ahx == "object":
                        bz["example"] = hb[1]
                        properties[zz[0]]["items"]["properties"][hb[0]] = bz
                    else:
                        properties[zz[0]]["items"]["properties"][hb[1]] = bz
                    i = i + 1
                    pass
            elif a_t_field is not None:
                properties[zz[0]]["example"] = zz[1]

        elif tz is not None:
            properties[zz[0]] = {
                "type": tz,
                "example": zz[1]
            }
        else:
            properties[zz[0]] = {
                "type": "string",
                "example": str(zz[1])
            }
    return properties


def build_example(obj: dict):
    for bb in obj.items():
        for ep in bb[1].items():
            print(f"Building response schema of '{bb[0]}'...")
            if "responses" not in ep[1]:
                print(f"No response schema was found in '{bb[0]}'.")
                continue
            for response in list(ep[1]["responses"].items()):
                a = response[1]
                if "example" not in a:
                    print("No example was found in response.")
                    continue
                ex = a["example"]
                schema = {}
                typ3 = whats_type_of_this_object(ex)
                schema["type"] = typ3
                if typ3 == "object":
                    schema["properties"] = b(ex)
                elif typ3 is not None:
                    schema["example"] = ex
                else:
                    schema["type"] = "string"
                    schema["example"] = str(ex)
                response[1]["schema"] = schema
                del response[1]["example"]
    return obj


def normalize_responses(obj: dict):
    normalized = {}

    for docs in obj.items():
        print(f"Normalizing responses of '{docs[0]}'...")

        doc = docs[1]["responses"]

        for methods in doc.items():
            staging = methods[1]

            staging["summary"] = staging["about"]
            del staging["about"]

            if type(staging["returns"]) is str:
                staging["produces"] = [staging["returns"]]
            else:
                staging["produces"] = staging["returns"]
            del staging["returns"]
            staging["responses"] = {}
            for code in list(staging.items()):
                if not str.isdecimal(str(code[0])):
                    continue

                coode = code[1]
                coode["description"] = coode["about"]
                del coode["about"]

                staging["responses"][code[0]] = code[1]
                del staging[code[0]]

            if "params" in docs[1]:
                staging["params"] = docs[1]["params"]
            if docs[0] not in normalized:
                normalized[docs[0]] = {}
            normalized[docs[0]] = dict(normalized[docs[0]], **{methods[0]: staging})

    return normalized


"""
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
"""


def convert_annotation(obj):
    swaggers = {}
    for oj in obj.items():
        if type(oj[1]) != endpoint.EndPoint:
            swaggers[oj[0]] = oj[1]
            continue
        file = oj[1]
        print(f"Importing docs from endpoint annotation '{file.method} {file.route_path}'...")
        file: endpoint.EndPoint
        doc = file.docs
        if doc is None:
            print(f"No additional documentation found in '{file.method} {file.route_path}'.")
            doc = endpoint.Document("No document")

        method = file.method.lower()

        security = []
        if file.auth_required:
            if doc.security is not None:
                security = doc.security
            else:
                security = None

        doc_obj = {
            method: dict({
                "about": doc.title,
                "returns": doc.types,
                "tags": doc.tags
            }, **doc.more)
        }

        if security is not None:
            doc_obj[method]["security"] = security

        print("Converting responses...")
        for response in doc.responses:
            d = doc_obj[method][response.code] = {
                "about": response.about
            }

            if doc.example is not None:
                d["example"] = doc.example
            if response.example is not None:
                d["example"] = response.example

        args = []

        path_args = []

        print("Converting arguments...")
        for arg in file.args:
            arg: endpoint.Argument
            norm_type = arg.norm_type()

            if arg.arg_in == "path":
                path_args.append(arg.name)

            st = {
                "name": arg.name,
                "in": arg.arg_in,
                "required": arg.required,
                "type": norm_type
            }
            arg_doc = arg.document
            if arg_doc is None:
                continue

            st["about"] = arg_doc.title

            if arg_doc.format is not None:
                st["format"] = arg_doc.format
            elif arg.type not in ["str", "string", "bool", "boolean", "other"]:
                at = None
                if arg.type == "float":
                    at = "float"
                elif arg.type in ["decimal", "double"]:
                    at = "double"
                elif "int" in arg.type:
                    at = "int32"
                elif arg.type == "long":
                    at = "int64"
                if at is not None:
                    st["format"] = at

            if norm_type == "string":
                if arg.min != -1:
                    st["minLength"] = arg.min
                if arg.max != -1:
                    st["maxLength"] = arg.max
            elif norm_type in ["integer", "number"]:
                if arg.min != -1:
                    st["minimum"] = arg.min
                if arg.max != -1:
                    st["maximum"] = arg.max

            st = dict(st, **arg_doc.more)

            args.append(st)

        path = file.route_path
        if not path.startswith("/"):
            path = "/" + path

        if file.path_arg:
            for path_arg in path_args:
                path = path.replace("__", "{" + path_arg + "}", 1)

        if path == "_":
            path = "/"
        elif path.endswith("/_"):
            path = path[:-1]

        if path not in swaggers:
            swaggers[path] = {}
            swaggers[path]["responses"] = {}
        if len(args) != 0:
            doc_obj[method]["parameters"] = args

        swaggers[path]["responses"] = dict(swaggers[path]["responses"], **doc_obj)

    return swaggers


def load_as_swagger(obj):
    swaggers = {}
    for file in obj:
        if type(file) == endpoint.EndPoint:
            swaggers[uuid.uuid4().hex] = file
            continue

        if file.endswith(".json"):
            with open(file, "r", encoding="utf-8") as j:
                doc = json.JSONDecoder().decode(j.read())
                if "docs" not in doc:
                    print(f"No docs were found in '{doc}'.")
                    continue
                print(f"Importing docs from endpoint json '{file}'...")
                path = file[:-5].replace("resources/handler", "")
                if re.match("^(.+?/|/)?_$", path):
                    path = path[:-1]
                swaggers[path] = {
                    "responses": doc["docs"]["responses"]
                }

    std = sorted(swaggers)
    tmp = {}
    for swg in std:
        tmp[swg] = swaggers[swg]
    return tmp


def load_as_module(obj):
    if hasattr(route, "loader"):
        loader = endpoint.loader
        loader.reload()
    else:
        loader = endpoint.EPManager()
        loader.load("src/server/handler_root/")

    loader.signals = []

    result = []

    for f in obj:
        if not f.endswith(".py"):
            result.append(f)
            continue
        loader.load_single(f)

    result += loader.enumerate()

    return result


def load_yaml(obj):
    global swagger
    printf("Loading template...")
    swagger = yaml.load(_SWAGGER_TEMPLATE, Loader=yaml.FullLoader)
    print("Done")
    return obj


def find():
    print("Searching modules...")
    docs = []
    for file in pathlib.Path("src/server/handler_root/").glob("**/*.py"):
        f = "/".join(file.parts)
        print("Found: " + f[:-3])
        if f in docs:
            print(f"ERROR: A conflict has occurred in {f[:3]}.")
        docs.append(f)
    print("Searching files...")
    for file in pathlib.Path("resources/handler/").glob("**/*"):
        f = "/".join(file.parts)
        print("Found: " + f)
        if f in docs:
            print(f"ERROR: A conflict has found in {f}.")
        docs.append(f)
    print(f"Found {len(docs)} endpoint(s).")
    print("Sorting...")
    return docs


steps = [
    find,
    load_yaml,
    load_as_module,
    load_as_swagger,
    convert_annotation,
    normalize_responses,
    build_example,
    normalize_params,
    build_swagger,
    save,
    generate_html
]

if __name__ == "__main__":
    print("Generating documents...")
    process_step(steps)
    docPath = os.path.abspath("docs.html")
    print(f"\n\nDocument generated successfully: {docPath}")


def gen():
    process_step(steps)
