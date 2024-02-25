# ABI2API

ABI2API-Alephium is a Python library for "converting" smart contract ABI (Application Binary Interface) on the Alephium blockchain into a RESTful API. It allows developers to expose the functionality of a smart contract through a simple API interface, making it easier to interact with Smart Contracts.

## Features

- Converts smart contract ABI into a RESTful API
- Supports GET methods for contract functions
- Generates API documentation using Swagger UI

# Installation

1. Clone the repository:

```bash
git clone https://github.com/SkullElf/ABI2API-Alephium.git
```
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

# Configuration

## Configuration - config.py
### Config Variables:
| Variable Name                                      | config.py                                 | Description                                  |
| -------------------------------------------------- | ----------------------------------------- | -----------------------------------------    |
| EnableManager                                      | EnableManager=True / False                | Enable / Disable the Manager app via `/`     |
| USERNAME                                           | USERNAME="admin" # Replace with something | Set the Username for the login to the Manager|
| PASSWORD                                           | PASSWORD="password" # Replace with pass   | Set the Password for the login to the Manager|
| PORT # Replace with port for the application       | PORT:  80                                 | Set the port you'd like to serve the APIs in |
| ENVIRONMENT # Replace with environment name        | ENVIRONMENT:  "mainnet"                   | Set the environment of the system            |
| ENVIRONMENTS # Fill as you see fit                 | "environment": "url of node"              | Add environments to the system               |

## Configuration - Manager app
ABIs are a collection of metatada about the contract.
To generate an API to interact with a Smart Contract, you will need to provide the app with several key details.
Prepare an ABI JSON, a SC address and pick a name for your API.

# Usage
## Setup
Update the config.py file with your specific configuration settings.
Once the app is running, enter the API Manager app using `http://localhost:80/` (assuming default settings were used).

Fill the following in the interface:
1. ABI JSON file or URL.
2. The corresponding Smart Contract address.
3. The name for the API (will be used in the URL).

Start the API server:

```
python main.py
```

Access the API documentation:
Open your web browser and visit http://localhost:80/NAME/ to view the Swagger UI documentation for the generated API (`NAME` being the app name specified in the config).

Make API requests:
You can now make GET requests to interact with your smart contract functions. Refer to the API documentation for the available endpoints and request formats.

> TIP 1: You can use the URL parameter `smartcontractaddress=X` to override the SC address in the same environment, and query SC X using the same ABI JSON.

> TIP 2: The `NAME` variable is a unique identifier, so make sure it's different in each entry.

## Example
For your convinience, a couple of APIs are already available in the system's database. Open the Manager app to interact with them.

# Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request.

# License
This project is licensed under the MIT License. See the LICENSE file for more information.
