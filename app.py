import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings

# Load Neo4j settings
settings = load_app_settings()
uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
os.environ["OLLAMA_API_URL"]="http://10.33.70.51:11434"
# Optional: Override LLM model if specified in settings
#OLLAMA_MODEL = settings.get('ollama', {}).get('model', 'mistral')
OLLAMA_MODEL = settings.get('ollama', {}).get('model', 'medllama2')

# Page Configuration
st.set_page_config(
    page_title="Medical GraphRAG Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Medical Case Assistant")
st.sidebar.success("Select a page above.")