import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
from components.ui_utils import get_neo4j_url_from_uri, format_metadata
from components.graphrag import DynamicGraphRAGChain

from dotenv import load_dotenv
load_dotenv()  # load .env file if it exists

# If using Streamlit secrets
if 'OPENAI_API_KEY' in st.secrets:
    os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']

# Load Neo4j settings
settings = load_app_settings()
uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
vector_index_name='admission_vector'

# Define the graph retrieval query for hybrid search
graph_retrieval_query = """
WITH node AS searchAdmission, score AS searchScore
MATCH (searchAdmission)
WITH searchAdmission, searchScore
MATCH (searchAdmission)-[:HAS_LAB]->(lab:LabEvent)
WITH searchAdmission, collect(lab) as labs, searchScore
MATCH (searchAdmission)-[:HAS_PRESCRIPTION]->(med:Prescription)
WITH searchAdmission, labs, collect(med) as meds, searchScore
OPTIONAL MATCH (searchAdmission)-[:HAS_NOTE]->(note:NoteEvent)
WITH searchAdmission, labs, meds, collect(note) as notes, searchScore
RETURN 
    searchAdmission.diagnosis AS text,
    searchScore AS score,
    {
        admission_id: searchAdmission.hadm_id,
        diagnosis: searchAdmission.diagnosis,
        labs: [lab IN labs | lab.itemid],
        medications: [med IN meds | med.drug],
        notes: [note IN notes | note.text],
        admission_type: searchAdmission.admission_type
    } AS metadata
ORDER BY score DESC
LIMIT 5
"""

# Initialize RAG chains
vector_chain = DynamicGraphRAGChain(
    neo4j_uri=uri,
    neo4j_username=user,
    neo4j_password=password,
    neo4j_database='neo4j',
    vector_index_name=vector_index_name,
    k=5
)

graph_vector_chain = DynamicGraphRAGChain(
    neo4j_uri=uri,
    neo4j_username=user,
    neo4j_password=password,
    neo4j_database='neo4j',
    vector_index_name=vector_index_name,
    graph_retrieval_query=graph_retrieval_query,
    k=5
)

def generate_prompt(query, patient_context=""):
    return f"""
    You are a medical assistant helping a doctor analyze patient cases. 
    Given the following query and patient context, provide insights based on similar cases in the database.
    
    Query: {query}
    Patient Context: {patient_context}
    
    Please analyze the cases provided in the context below and provide:
    1. A summary of relevant similar cases
    2. Key patterns or insights observed
    3. Potential considerations for the current case
    
    Base your analysis only on the information provided in the context.
    """

# Sidebar for patient context
with st.sidebar:
    st.header("Patient Context")
    patient_context = st.text_area(
        "Enter relevant patient information (optional)",
        height=150
    )

# Main query interface
st.header("Medical Query")
query = st.text_area("Enter your medical query:", height=100)

col1, col2 = st.columns(2)

if query:
    with col1:
        st.subheader("Vector Search Results")
        with st.spinner('Running Vector Search...'):
            with st.expander('Response:', True):
                st.markdown(vector_chain.invoke(
                    generate_prompt(query, patient_context),
                    retrieval_search_text=query
                ))
            with st.expander("Search Context"):
                st.json(vector_chain.last_used_context)
            with st.expander("Search Query"):
                queries = vector_chain.get_last_browser_queries()
                st.code(queries['params_query'], language='cypher')
                st.code(queries['query_body'], language='cypher')

    with col2:
        st.subheader("Hybrid Graph-Vector Results")
        with st.spinner('Running Hybrid Search...'):
            with st.expander('Response:', True):
                st.markdown(graph_vector_chain.invoke(
                    generate_prompt(query, patient_context),
                    retrieval_search_text=query
                ))
            with st.expander("Search Context"):
                st.json(graph_vector_chain.last_used_context)
            with st.expander("Search Query"):
                queries = graph_vector_chain.get_last_browser_queries()
                st.code(queries['params_query'], language='cypher')
                st.code(queries['query_body'], language='cypher')

# Add example queries
with st.sidebar:
    st.header("Example Queries")
    example_queries = [
        "Find similar cases of CORONARY ARTERY DISEASE with abnormal lab values",
        "What are common medication patterns for urology patients?",
        "Show cases with similar admission patterns and outcomes",
    ]
    
    if st.button("Try Example Query 1"):
        st.session_state.query = example_queries[0]
    if st.button("Try Example Query 2"):
        st.session_state.query = example_queries[1]
    if st.button("Try Example Query 3"):
        st.session_state.query = example_queries[2]