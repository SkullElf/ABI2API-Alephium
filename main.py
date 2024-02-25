from quart import Quart, jsonify, request, redirect, render_template, Response
import asyncio
from marshmallow import Schema, fields, EXCLUDE
import sqlite3
import re
from base64 import b64decode
from typing import Dict, Union
from functools import wraps
import json
import requests
import uvicorn
import os
import aiohttp

from abiconverter import convert_abi
from config import USERNAME, PASSWORD, PORT, DB_PATH, EnableManager, PROXY_URL
from dark_theme_css import CSS

app = Quart(__name__)
CONFIG_DICT = {}


async def query_sc(sc_address, func, endpoints, args=None):
    if args is None:
        args = []
    endpoint_data = next((d for d in endpoints if d['name'] == func), None)
    if endpoint_data is None:
        return None
    body = {
        "args": args,
        "group": 0,
        "address": sc_address,
        "methodIndex": endpoint_data["endpointIndex"]
    }
    url = f"{PROXY_URL}contracts/call-contract"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=body) as response:
            try:
                output = []
                response_json = await response.json()
                for item in response_json["returns"]:
                    output.append(item["value"])
                if len(output) == 1:
                    output = output[0]
                return 200, {"output": output}

            except:
                return 500, "Failed to load JSON response from gateway"


def requires_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_type, auth_string = auth_header.split(' ')
            auth_string = b64decode(auth_string).decode('utf-8')
            username, password = auth_string.split(':')
            if username == USERNAME and password == PASSWORD:
                return await f(*args, **kwargs)
        return Response('Please authenticate', 401, {'WWW-Authenticate': 'Basic realm="Login!"'})
    return decorated


async def api_docs(name) -> str:
    swagger_ui_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ABI2API - {name.replace('/', '')}</title>
        <link rel="icon" type="image/png" size="32x32" href="https://explorer.alephium.org/favicon.ico">
        <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.52.1/swagger-ui.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.52.1/swagger-ui-bundle.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.52.1/swagger-ui-standalone-preset.min.js"></script>

        <style>
    ''' + CSS + '''

  </style>
    </head>
    <body>
<div class="topbar"><div class="wrapper"><div class="topbar-wrapper"><center><img src="https://cdn.discordapp.com/attachments/1002615966598967358/1131252032616005812/new_logo.png?ex=65e8910e&is=65d61c0e&hm=437ffbd0ccef5818fa7a8b5ff2c84c21495359544443716d28969ac47375c198&" height=50% width=50%/></center></div></div></div>
        <div id="swagger-ui"></div>
        <script>
            SwaggerUIBundle({
                url: window.location.origin + "/" + ''' + f"'{name}/{name}swagger.json'," + '''
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ]
            });
        </script>
    </body>

    </html>
    '''
    return swagger_ui_html


def resolve_input_type(input_type) -> str:
    cleaned_type = re.sub(r"<.*?>", "", input_type)
    cleaned_type = re.sub(r"optional|variadic", "", cleaned_type)
    datatypes = {
        "BigUint": "integer",
        "u64": "integer",
        "Address": "string",
        "bool": "boolean",
        "TokenIdentifier": "string",
        "EgldOrEsdtTokenIdentifier": "string",
        "u32": "integer",
        "u8": "integer"
    }
    return datatypes.get(cleaned_type, "string")


def resolve_output_type(output_type: Union[str, Dict]) -> Dict:
    basic_types = {
        'I256': {'type': 'integer', 'example': 12345678},
        'U256': {'type': 'integer', 'example': 12345678},

        'ByteVec': {'type': 'string', 'example': 'When the time of the White Frost comes, do not eat the yellow snow!'},
        'Bool': {'type': 'boolean', 'example': False},
        'BigUint': {'type': 'string', 'example': '69000000000000000000'},
        'BigInt': {'type': 'string', 'example': '69000000000000000000'},

        'Address': {'type': 'string', 'example': '1AfBFvSU92Sp1GTgFQKD4LQN91vXj22GijqVztpC56ozA'},

        'Array': {'type': 'list', 'example': ['one', 'two']}
    }

    if isinstance(output_type, list):
        output_type = output_type[0]

    if isinstance(output_type, str):
        resolved_type = None
        if output_type in basic_types:
            resolved_type = basic_types[output_type]
        return resolved_type
    else:
        # If the output type is not a string, it means it's already resolved, so return as is
        return output_type


class ABITypeSchema(Schema):
    class Meta:
        ordered = True
        unknown = EXCLUDE

    name = fields.Str(required=True)
    mutability = fields.Str(required=True)
    inputs = fields.List(fields.Dict(), required=True)
    outputs = fields.List(fields.Dict())


def generate_custom_swagger_json(name: str = "") -> Dict:
    display_name = name.replace('/', '')
    # Generate the Swagger JSON specification
    swagger_json = {
        'swagger': '2.0',
        'info': {
            'title': f"ABI2API - API for Smart Contract: {CONFIG_DICT[display_name]['abi_json']['name']}",
            'description': f'## Description\nSwagger API documentation for ABI JSON on the Alephium Blockchain.\n## Credits\nBuilt by: SkullElf\nFeel free to follow Bobbet on <a href=\"https://twitter.com/BobbetBot\">Twitter</a>\n\n## Details\nThis API instance provides data from a smart contract in the address: <a href=\"https://explorer.alephium.org/addresses/{CONFIG_DICT[display_name]["SCADDRESS"]}\">{CONFIG_DICT[display_name]["SCADDRESS"]}</a>',
            'version': '1.0'
        },
        'paths': {},
        'definitions': {},
        'tags': [
            {
                'name': name.replace('/', ''),
                'description': f'Endpoints with `readonly` mutability for smart contract: `{name.replace("/", "")}`'
            }
        ]
    }

    for endpoint in CONFIG_DICT[display_name]["endpoints"]:
        if endpoint["mutability"] == "mutable":
            continue
        schema = ABITypeSchema()
        endpoint_data = schema.load(endpoint)
        # Generate the path for the Swagger JSON specification
        swagger_path = f"/{name}/{endpoint['name']}"
        swagger_parameters = []
        for input_data in endpoint_data['inputs']:
            input_name = input_data['name']
            input_type = input_data['type']
            is_optional = input_type.startswith("optional")
            swagger_parameter = {
                'name': input_name,
                'in': 'query',
                'required': not is_optional
            }
            if input_type == "Array":
                swagger_parameter['type'] = 'array'
                swagger_parameter['items'] = {
                    'type': 'string'
                }
            elif input_type == "U256":
                swagger_parameter['type'] = 'integer'
            else:
                swagger_parameter['type'] = 'string'
            swagger_parameters.append(swagger_parameter)
        # Additional handling for the "docs" field
        if "docs" in endpoint:
            description = "\n".join(endpoint["docs"])
        else:
            description = f"No documentation available for {endpoint['name']}."
        swagger_json['paths'][swagger_path] = {
            'get': {
                'summary': endpoint['name'],
                'description': description,
                'parameters': swagger_parameters,
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                output_data.get('name', 'output'): resolve_output_type(
                                    output_data.get('type', 'output'))
                                for output_data in endpoint.get('outputs', [])
                            }
                        }
                    }
                },
                'tags': [display_name]
            }
        }
        # Generate the definition for the Swagger JSON specification
        swagger_definition = {
            'type': 'object',
            'properties': {
                output_data.get('name', 'output'): resolve_output_type(output_data.get('type', 'output'))
                for output_data in endpoint.get('outputs', [])
            }
        }
        swagger_json['definitions'][f"{endpoint['name']}_response"] = swagger_definition
        # Update the Swagger parameter to represent the Array input as an array
        for parameter in swagger_parameters:
            if parameter['name'] in endpoint_data['inputs']:
                parameter['x-multi-item'] = True

    return swagger_json


@app.route('/<name>/<path:path>', methods=['GET'])
async def dynamic_route(name, path):
    if path.endswith('.json'):
        return jsonify(generate_custom_swagger_json(name))
    inputs = {}
    args = []
    scaddress = str(request.args.get("smartcontractaddress", default=CONFIG_DICT[name]["SCADDRESS"]))
    endpoint_data = next((item for item in CONFIG_DICT[name]["endpoints"] if item["name"] == path), None)
    for input_data in endpoint_data['inputs']:
        input_name = input_data['name']
        input_value = str(request.args.get(input_name, default=''))
        input_type = input_data['type']
        is_multi_arg = input_type == "Array"

        if is_multi_arg:
            input_values = input_value.split(',')
            inputs[input_name] = input_values
        else:
            inputs[input_name] = input_value

        args.append({
            "value": str(input_value),
            "type": input_data["type"]
        })

    # Process the input and call the smart contract based on the endpoint name
    output = await query_sc(scaddress, path, CONFIG_DICT[name]["endpoints"], args)
    code, output = output
    if code != 200:
        message = {"error": output}
        response = jsonify(message)
        response.status_code = code
        return response
    return jsonify(output)


def create_database_and_table():
    global conn

    # Check if the directory "databases" exists, if not, create it
    if not os.path.exists("databases"):
        os.makedirs("databases")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the "abis" table if it does not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abis (
        SCADDRESS TEXT NOT NULL,
        ABI_PATH TEXT NOT NULL,
        NAME TEXT NOT NULL
    );
    """)

    # Commit the transaction and close the connection
    conn.commit()


async def config():
    # Call the function to create the database and table
    create_database_and_table()

    rows = conn.execute("SELECT * FROM abis").fetchall()
    for row in rows:
        sc_address, abi_path, name = row
        name += "/"

        if abi_path.startswith("https://") or abi_path.startswith("http://"):
            abi_json = requests.get(abi_path).json()
            abi_json = convert_abi(abi_json)
            dummy = []
            for endpoint in abi_json["endpoints"]:
                if endpoint["mutability"] == "readonly":
                    dummy.append(endpoint)
        else:
            # Load ABI JSON from file
            with open(abi_path) as f:
                abi_json = json.load(f)
        for endpoint in abi_json["endpoints"]:
            if "inputs" not in endpoint:
                endpoint["inputs"] = []
        endpoints = abi_json["endpoints"]
        CONFIG_DICT[name.replace('/', '')] = {
            "abi_json": abi_json,
            "endpoints": endpoints,
            "SCADDRESS": sc_address
        }


async def update_config():
    while True:
        await config()
        await asyncio.sleep(3600)


@app.route('/<name>/', methods=['GET'])
async def dynamic_swagger(name):

    rows = conn.execute("SELECT * FROM abis WHERE NAME=?", [name]).fetchall()
    if len(rows) > 0:
        return await api_docs(name)

    return jsonify({'error': 'This API was not found'}), 404


async def create_update_task():
    asyncio.create_task(update_config())


def activate_config_manager():
    def is_valid_json(content: str) -> bool:
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False

    @app.route('/remove_api/<int:api_index>', methods=['GET'])
    @requires_auth
    async def remove_api(api_index):
        rows = conn.execute("SELECT * FROM abis").fetchall()
        if (api_index + 1) <= len(rows):
            sc_address, abi_path, name = rows[api_index]
            conn.execute("DELETE FROM abis WHERE NAME=? AND SCADDRESS=?", (name, sc_address))
            conn.commit()

        return redirect('/')

    @app.route('/add_api', methods=['POST'])
    @requires_auth
    async def add_api():
        # Process the form data and update the config file
        data = await request.form
        data = data.to_dict()
        sc_address = data['sc_address']
        api_name = data['api_name']
        input_type = data['input_type']

        # Determine whether the user provided a file or a URL for the ABI JSON
        if input_type == 'file':
            # Handle the file upload
            files = (await request.files).to_dict()
            abi_file = files.get('abi_file')

            # Read the file content
            abi_content = abi_file.read().decode()
            if not is_valid_json(abi_content):
                response = jsonify({"Error: ABI JSON is not a valid JSON"})
                response.status_code = 400
                return response
            abi_content = json.dumps(convert_abi(json.loads(abi_content)), indent=4)
            # Check if the directory "abis" exists, if not, create it
            if not os.path.exists("abis"):
                os.makedirs("abis")
            with open(f"./abis/{api_name}.json", "w") as outfile:
                outfile.write(abi_content)
            abi_path = f"./abis/{api_name}.json"
        else:
            # Handle the URL input
            abi_path = data['abi_url']

        rows = conn.execute("SELECT * FROM abis WHERE name=?", [api_name]).fetchall()
        if len(rows) == 0:
            conn.execute("INSERT INTO abis VALUES(?,?,?)", (
                sc_address,
                abi_path,
                api_name
            ))
            conn.commit()
            await config()
        else:
            response = jsonify({"Error: API name already exists"})
            response.status_code = 400
            return response
        return redirect('/')

    @app.route('/', methods=['GET', 'POST'])
    @requires_auth
    async def index():
        if request.method == 'POST':
            return await add_api()
        api_list = []
        rows = conn.execute("SELECT * FROM abis").fetchall()
        for row in rows:
            sc_address, abi_path, name = row
            api_list.append({
                "SCADDRESS": sc_address,
                "ABI_PATH": abi_path,
                "NAME": name
            })
        return await render_template('index.html', api_list=api_list, enumerate=enumerate)


if __name__ == "__main__":
    if EnableManager:
        activate_config_manager()
    asyncio.run(create_update_task())
    uvicorn.run(app, port=PORT, host="0.0.0.0")
