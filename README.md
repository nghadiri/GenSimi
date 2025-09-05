# GenSimi - Medical GraphRAG Assistant

A medical GraphRAG (Graph Retrieval-Augmented Generation) assistant that analyzes patient cases using the MIMIC-III dataset. The application provides multiple analysis approaches including vector search, graph-based retrieval, and hybrid methods to help with medical case analysis.

## Features

- **Multi-Modal Analysis**: Three different approaches to analyze medical cases
  - Vector Search: Text similarity-based case retrieval
  - Graph Analysis: Relationship-based medical entity retrieval  
  - Hybrid Analysis: Combined vector and graph-based approach
- **Medical Data Integration**: Works with MIMIC-III dataset stored in Neo4j
- **Interactive Web Interface**: Streamlit-based UI with side-by-side analysis comparison
- **Contextual Query Processing**: Tailored prompts based on query type (medications, labs, outcomes)

## Quick Start

### Prerequisites

- Python 3.8+
- Neo4j database with MIMIC-III data
- Ollama server running MedLLaMA2 model

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gensimi
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `AppSettings.json`:
```json
{
    "neo4j": {
        "uri": "your_neo4j_uri",
        "user": "neo4j",
        "password": "your_password"
    },
    "ollama": {
        "model": "medllama2"
    }
}
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open the web interface in your browser
2. Enter patient context (optional) in the sidebar
3. Submit a medical query such as:
   - "What are typical lab patterns for patients with high creatinine?"
   - "What medication combinations are used for urology patients?"
   - "Show cases with similar admission patterns"
4. Compare results across the three analysis approaches
5. Expand "Case Details" to see the underlying data used for analysis

## Architecture

- **Main App**: `app.py` - Streamlit web interface
- **GraphRAG Engine**: `components/graphrag.py` - Core RAG implementations
- **Configuration**: `util/config.py` - Settings management
- **Data Processing**: `vgsimi/` - Neo4j data loading scripts
- **Additional Pages**: `pages/` - Extra Streamlit functionality

## Contributing

This project works with sensitive medical data. Ensure compliance with data protection regulations when contributing.