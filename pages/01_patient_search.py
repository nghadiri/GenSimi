import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
from components.ui_utils import get_neo4j_url_from_uri, format_metadata
from components.graphrag import DynamicGraphRAGChain, GraphRAGChain

from dotenv import load_dotenv
load_dotenv()  # load .env file if it exists

# Load Neo4j settings
settings = load_app_settings()
uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
vector_index_name = 'admission_vector'

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

# Function to run all analyses
def run_analysis(query, patient_context=""):
    vector_response = vector_chain.invoke(
        generate_prompt(query, patient_context),
        retrieval_search_text=query
    )
    
    graph_response = graph_chain.invoke(
        generate_prompt(query, patient_context)
    )
    
    hybrid_response = graph_vector_chain.invoke(
        generate_prompt(query, patient_context),
        retrieval_search_text=query
    )
    
    return {
        'vector': {
            'response': vector_response,
            'context': vector_chain.last_used_context
        },
        'graph': {
            'response': graph_response,
            'context': graph_chain.last_used_context
        },
        'hybrid': {
            'response': hybrid_response,
            'context': graph_vector_chain.last_used_context
        }
    }