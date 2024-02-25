import json


def convert_to_new_structure(old_dict):
    # Initialize the new dictionary with the function name and mutability based on 'isPublic'
    new_dict = {
        "name": old_dict["name"],
        "mutability": "readonly" if old_dict.get("isPublic", False) else "mutable",
        "inputs": [],
        "outputs": []
    }

    # Convert the parameters (inputs) from the old structure to the new one
    for param_name, param_type in zip(old_dict.get("paramNames", []), old_dict.get("paramTypes", [])):
        new_dict["inputs"].append({
            "name": param_name,
            "type": param_type  # Direct mapping; adjust if necessary for different type systems
        })

    # Convert the return types (outputs) from the old structure to the new one
    for return_type in old_dict.get("returnTypes", []):
        new_dict["outputs"].append({
            "type": return_type  # Direct mapping; adjust if necessary for different type systems
        })

    return new_dict


def convert_abi(abi_json):
    new_abi = {
        "name": abi_json["name"]
    }
    new_endpoints = []
    index = 0
    for endpoint in abi_json["functions"]:

        if len(endpoint["returnTypes"]) > 0 and endpoint["isPublic"]:
            new_endpoint = convert_to_new_structure(endpoint)
            new_endpoint["endpointIndex"] = index
            new_endpoints.append(new_endpoint)

        index += 1
    new_abi["endpoints"] = new_endpoints
    return new_abi
