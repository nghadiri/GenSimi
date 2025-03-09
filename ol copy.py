import requests

def list_llms(server_url):
    try:
        # Specify the endpoint for listing available LLMs
        endpoint = f"{server_url}/api/tags"

        # Send a GET request to the server
        response = requests.get(endpoint)

        # Check if the request was successful
        if response.status_code == 200:
            models = response.json()
            print(f"Available LLMs on the server: {models}")
            for model in models["models"]:
                print(f"- {model.name}")
        else:
            print(f"Failed to retrieve models. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Replace with your Ollama server URL
ollama_server_url = "http://10.33.70.51:11434"
list_llms(ollama_server_url)
