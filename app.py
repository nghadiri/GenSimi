import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
from components.ui_utils import get_neo4j_url_from_uri, format_metadata
from components.graphrag import DynamicGraphRAGChain, GraphRAGChain

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

# Define the improved graph retrieval query
graph_retrieval_query = """
MATCH (admission:Admission)
WHERE admission.hadm_id IS NOT NULL
WITH admission
MATCH (admission)-[:HAS_LAB]->(lab:LabEvent)
WITH admission, collect(lab) as labs
OPTIONAL MATCH (admission)-[:HAS_PRESCRIPTION]->(med:Prescription)
WITH admission, labs, collect(med) as meds
OPTIONAL MATCH (admission)-[:HAS_NOTE]->(note:NoteEvent)
WITH admission, labs, meds, collect(note) as notes

WITH admission, labs, meds, notes,
     size(labs) * 0.4 +
     size(meds) * 0.3 +
     size(notes) * 0.3 as relevanceScore

RETURN 
    admission.diagnosis AS text,
    relevanceScore as score,
    {
        admission_id: admission.hadm_id,
        diagnosis: admission.diagnosis,
        labs: [l IN labs | {
            id: l.itemid,
            name: l.label,
            value: l.valuenum,
            units: l.valueuom,
            flag: l.flag
        }],
        medications: [m IN meds | {
            name: m.drug,
            dosage: m.dose_val_rx,
            units: m.dose_unit_rx
        }],
        notes: [n IN notes | n.text],
        admission_type: admission.admission_type,
        length_of_stay: duration.between(admission.admittime, admission.dischtime).days,
        discharge_location: admission.discharge_location
    } AS metadata
ORDER BY score DESC
"""

# Initialize RAG chains with consistent k value
k_value = 3
vector_chain = DynamicGraphRAGChain(
    neo4j_uri=uri,
    neo4j_username=user,
    neo4j_password=password,
    neo4j_database='neo4j',
    vector_index_name=vector_index_name,
    k=k_value
)

graph_chain = GraphRAGChain(
    neo4j_uri=uri,
    neo4j_username=user,
    neo4j_password=password,
    neo4j_database='neo4j',
    vector_index_name=vector_index_name,
    graph_retrieval_query=graph_retrieval_query,
    k=k_value
)

graph_vector_chain = DynamicGraphRAGChain(
    neo4j_uri=uri,
    neo4j_username=user,
    neo4j_password=password,
    neo4j_database='neo4j',
    vector_index_name=vector_index_name,
    graph_retrieval_query=graph_retrieval_query,
    k=k_value
)

def generate_prompt(query, patient_context=""):
    """Generate a focused prompt based on the query type"""
    query_lower = query.lower()
    
    # Identify query type and add specific instructions
    if any(word in query_lower for word in ["medication", "drug", "prescription"]):
        focus = "medication patterns, drug combinations, and dosages"
    elif any(word in query_lower for word in ["lab", "test", "value", "cr", "bun"]):
        focus = "lab values, abnormal results, and lab value patterns"
    elif any(word in query_lower for word in ["outcome", "pattern", "admission", "discharge"]):
        focus = "admission patterns, length of stay, and outcomes"
    else:
        focus = "all relevant clinical information"
    
    return f"""
    You are a medical assistant analyzing patient cases to answer the following specific query:
    
    Query: {query}
    Patient Context: {patient_context}
    
    Focus your analysis on {focus}. For each point you make:
    1. Reference specific admission IDs (e.g., "In admission XXXX...")
    2. Provide concrete examples from the cases
    3. Note any relevant patterns
    4. Mention any limitations in the available data
    
    Base your analysis ONLY on the information provided in the context below.
    """

# Main interface
st.title("Medical Case Assistant")

# Sidebar for patient context and examples
with st.sidebar:
    st.header("Patient Context")
    patient_context = st.text_area(
        "Enter relevant patient information (optional)",
        height=150,
        help="Add any relevant patient information to provide context for the query"
    )
    
    st.header("Example Queries")
    example_queries = [
        "What are the typical lab patterns for patients with high creatinine levels?",
        "What medication combinations are commonly used for urology patients with hypertension?",
        "Show me cases with similar admission patterns and their outcomes",
        "What are the typical length of stay patterns for patients with kidney-related diagnoses?"
    ]
    
    for i, query in enumerate(example_queries, 1):
        if st.button(f"Try Example {i}", key=f"example_{i}"):
            st.session_state.query = query

# Main query interface
st.header("Medical Query")
query = st.text_area(
    "Enter your medical query:",
    height=100,
    help="Ask about patient cases, lab patterns, medications, or outcomes"
)

if query:
    st.info("Analyzing cases using vector, graph, and hybrid approaches...")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Vector Search Analysis")
        with st.expander("Response", expanded=True):
            vector_response = vector_chain.invoke(
                generate_prompt(query, patient_context),
                retrieval_search_text=query
            )
            st.markdown(vector_response)
        
        with st.expander("Case Details"):
            st.json(vector_chain.last_used_context)
    
    with col2:
        st.subheader("Graph Analysis")
        with st.expander("Response", expanded=True):
            graph_response = graph_chain.invoke(
                generate_prompt(query, patient_context)
            )
            st.markdown(graph_response)
        
        with st.expander("Case Details"):
            st.json(graph_chain.last_used_context)
    
    with col3:
        st.subheader("Hybrid Analysis")
        with st.expander("Response", expanded=True):
            hybrid_response = graph_vector_chain.invoke(
                generate_prompt(query, patient_context),
                retrieval_search_text=query
            )
            st.markdown(hybrid_response)
        
        with st.expander("Case Details"):
            st.json(graph_vector_chain.last_used_context)
    
    # Add a section for comparing results
    st.header("Analysis Summary")
    st.write("""
    The analysis above shows results from three different approaches:
    1. Vector Search: Uses text similarity to find relevant cases
    2. Graph Analysis: Uses relationships between medical entities
    3. Hybrid Approach: Combines both vector and graph-based analysis
    
    Expand the 'Case Details' under each analysis to see the raw data used for the analysis.
    """)

else:
    st.info("Enter a medical query above to analyze similar cases")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("📋 All analyses are based on available case data")