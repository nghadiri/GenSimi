import json

def load_app_settings(file_path='AppSettings.json'):
    try:
        with open(file_path, 'r') as file:
            settings = json.load(file)
            return settings
    except FileNotFoundError:
        print(f"Settings file {file_path} not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return {}
