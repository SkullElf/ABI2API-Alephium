from quart import Quart, render_template, request, redirect
import json
import asyncio
import requests
from api import run_app
from threading import Thread
import time
import subprocess
app = Quart(__name__)

CONFIG_PATH = "config.json"  # Your config file path

# Load existing config data from a JSON file
def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            data = json.load(file)
            #print("Loaded data from config.json:", data)  # Add this line for debugging
            return data
    except FileNotFoundError:
        return {"APIS": []}

@app.route('/remove_api/<int:api_index>', methods=['GET'])
async def remove_api(api_index):
    # Read the existing config file
    with open(CONFIG_PATH) as f:
        config_data = json.load(f)

    # Remove the API configuration at the specified index
    if 0 <= api_index < len(config_data["APIS"]):
        config_data["APIS"].pop(api_index)

        # Write the modified data back to the config file
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config_data, f)
    # Redirect back to the index page
    return redirect('/')

@app.route('/add_api', methods=['POST'])
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
        with open(f"./abis/{api_name}.json", "w") as outfile:
            outfile.write(abi_content)
        abi_path = f"./abis/{api_name}.json"
    else:
        # Handle the URL input
        abi_path = data['abi_url']

    # Read the existing config file
    with open(CONFIG_PATH) as f:
        config_data = json.load(f)

    # Add the new API configuration
    new_api_config = {
        "SCADDRESS": sc_address,
        "ABI_PATH": abi_path,
        "NAME": api_name
    }
    config_data["APIS"].append(new_api_config)

    # Write the modified data back to the config file
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f)
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        return await add_api()

    config_data = load_config()
    api_list = config_data["APIS"]
    return await render_template('index.html', api_list=api_list, enumerate=enumerate)


if __name__ == '__main__':
    asyncio.run(app.run(host='127.0.0.1', port=5000, debug=True))