# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GenSimi is a medical GraphRAG (Graph Retrieval-Augmented Generation) assistant that analyzes patient cases using the MIMIC-III dataset stored in Neo4j. The application provides three different analysis approaches: vector search, graph-based retrieval, and hybrid analysis.

## Architecture

### Core Components

- **Main Application**: `app.py` - Streamlit-based web interface with three-column analysis layout
- **GraphRAG Engine**: `components/graphrag.py` - Contains multiple RAG chain implementations:
  - `GraphRAGChain` - Pure graph-based retrieval
  - `DynamicGraphRAGChain` - Hybrid vector + graph approach
  - `GraphRAGText2CypherChain` - Natural language to Cypher query conversion
  - `GraphRAGPreFilterChain` - Pre-filtered graph search
- **Configuration**: `util/config.py` - Loads settings from AppSettings.json
- **UI Utilities**: `components/ui_utils.py` - Helper functions for the interface

### Database Architecture

The application connects to Neo4j databases containing MIMIC-III medical data with the following key node types:
- `Admission` - Hospital admissions (main vector index target)
- `LabEvent` - Laboratory test results
- `Prescription` - Medication data
- `NoteEvent` - Clinical notes

Relationships connect admissions to their associated lab results, prescriptions, and notes via `HAS_LAB`, `HAS_PRESCRIPTION`, and `HAS_NOTE` relationships.

## Development Commands

### Running the Application

```bash
# Run the Streamlit app
streamlit run app.py
```

### Python Dependencies

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `transformers>=4.30.0` - For embeddings and NLP
- `torch>=2.0.0` - PyTorch for ML models
- `medspacy==1.2.0` - Medical text processing
- `streamlit` - Web interface framework
- LangChain ecosystem for RAG implementation

## Configuration

### Database Configuration

The application uses `AppSettings.json` for configuration:

```json
{
    "neo4j": {
        "uri": "neo4j+s://your-instance.databases.neo4j.io",
        "user": "neo4j",
        "password": "your_password"
    },
    "ollama": {
        "model": "medllama2"
    }
}
```

Configuration variants:
- `AppSettings.json` - Main configuration
- `AppSettings-d.json` - Development settings
- `AppSettings-l.json` - Local settings

### LLM Configuration

The system uses Ollama with MedLLaMA2 model by default, with OpenAI embeddings for vector similarity. The Ollama API endpoint is configured to `http://10.33.70.51:11434`.

## Key Technical Details

### Vector Index

The application expects a vector index named `vector_index_name` (this variable needs to be defined in the main app) on the `Admission` nodes in Neo4j, using OpenAI's `text-embedding-ada-002` model.

### Graph Retrieval Query

The core graph retrieval query combines admission data with related medical information, scoring relevance based on the number of associated labs (40%), medications (30%), and notes (30%).

### Development Utilities

- `vgsimi/` directory contains data loading and processing scripts for Neo4j
- `pages/` directory contains additional Streamlit pages (`01_patient_search.py`)
- `misc/`, `ced/`, `trans/`, `uttree/`, `mimic-iii-sql/` directories contain supporting data and SQL files

## Important Notes

- The application hardcodes the Ollama API URL and expects a specific Neo4j schema
- Medical data requires careful handling - ensure compliance with data protection regulations
- The system is designed specifically for MIMIC-III dataset structure
- Vector embeddings and graph relationships must be pre-established in Neo4j before use