import json
import os

def read_json_file(file_path):
    """
    Reads and parses a JSON file safely.
    
    :param file_path: Path to the JSON file.
    :return: Parsed Python object (dict, list, etc.) or None if error occurs.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format. Details: {e}")
    except OSError as e:
        print(f"Error reading file: {e}")
    
    return None


# This will run immediately when the file is imported or executed
file_path = "letters.json" 
json_data = read_json_file(file_path)

if json_data is not None:
    print("JSON content loaded successfully:")
    # print(json.dumps(json_data, indent=4))