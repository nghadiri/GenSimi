import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
from pages.patient_search import run_analysis

# Page Configuration
st.set_page_config(
    page_title="Medical GraphRAG Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Run all analyses
    results = run_analysis(query, patient_context)
    
    # Display results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Vector Search Analysis")
        with st.expander("Response", expanded=True):
            st.markdown(results['vector']['response'])
        with st.expander("Case Details"):
            st.json(results['vector']['context'])
    
    with col2:
        st.subheader("Graph Analysis")
        with st.expander("Response", expanded=True):
            st.markdown(results['graph']['response'])
        with st.expander("Case Details"):
            st.json(results['graph']['context'])
    
    with col3:
        st.subheader("Hybrid Analysis")
        with st.expander("Response", expanded=True):
            st.markdown(results['hybrid']['response'])
        with st.expander("Case Details"):
            st.json(results['hybrid']['context'])
    
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