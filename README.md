# GenSimi - Medical GraphRAG Assistant

A medical GraphRAG (Graph Retrieval-Augmented Generation) assistant that analyzes patient cases using the MIMIC-III dataset. Building upon the patient similarity assessment framework from [Patient-Similarity-through-Representation](https://github.com/HodaMemar/Patient-Similarity-through-Representation), this work extends the approach by integrating Graph Retrieval-Augmented Generation techniques to provide enhanced medical case analysis through multiple retrieval strategies.

## About This Work

This project extends the patient similarity assessment methodology described in:

> Memarzadeh, H., Ghadiri, N., Samwald, M., & Lotfi Shahreza, M. (2022). "A study into patient similarity through representation learning from medical records". Knowledge and Information Systems, 64(12), 3293-3324.

The original work presented a novel data representation method for electronic medical records (EMRs) that considers information in clinical narratives. Patient similarity measurement requires converting heterogeneous EMRs into comparable formats to calculate distance. The study proposed an unsupervised approach for building patient representations that integrate unstructured and structured data extracted from patients' EMRs, employing tree structures to model extracted data that capture temporal relations of multiple medical events.

**GenSimi extends this foundation by:**
- Implementing GraphRAG techniques that combine traditional vector similarity with graph-based medical knowledge retrieval
- Providing multiple analysis approaches (vector search, graph-based retrieval, and hybrid methods) for comprehensive case analysis  
- Integrating real-time query processing with contextual medical reasoning using large language models
- Offering an interactive web interface for comparative analysis across different retrieval strategies
- **UTTree V2 Pipeline**: Modern implementation with advanced embeddings and vector databases for scalable patient similarity assessment

## Features

### Core GraphRAG Analysis
- **Multi-Modal Analysis**: Three different approaches to analyze medical cases
  - Vector Search: Text similarity-based case retrieval
  - Graph Analysis: Relationship-based medical entity retrieval  
  - Hybrid Analysis: Combined vector and graph-based approach
- **Medical Data Integration**: Works with MIMIC-III dataset stored in Neo4j
- **Interactive Web Interface**: Streamlit-based UI with side-by-side analysis comparison
- **Contextual Query Processing**: Tailored prompts based on query type (medications, labs, outcomes)

### UTTree V2 Patient Similarity Pipeline
- **Advanced Embeddings**: mxbai-embed-large model via Ollama for superior patient representations
- **Vector Database**: Weaviate integration for scalable similarity search and storage
- **Temporal Tree Construction**: Implements UTTree methodology with Weisfeiler-Lehman relabeling
- **Modern NLP**: Integrated ScispaCy and MedspaCy for clinical concept extraction
- **Real-time Similarity Search**: Sub-second patient similarity assessment
- **GraphRAG Integration**: Seamless linking between vector embeddings and Neo4j graph data

## Quick Start

### Prerequisites

#### Core GraphRAG Application
- Python 3.8+
- Neo4j database with MIMIC-III data
- Ollama server running MedLLaMA2 model

#### UTTree V2 Pipeline (Optional)
- Weaviate vector database
- Ollama server with mxbai-embed-large model
- ScispaCy medical NLP models

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

3. Configure your settings:

**AppSettings.json** (Core application):
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

**.env file** (UTTree V2 pipeline):
```bash
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=mxbai-embed-large
WEAVIATE_URL=http://localhost:8080
```

4. Run the application:
```bash
# Core GraphRAG interface
streamlit run app.py

# UTTree V2 pipeline (generate patient similarities)
cd uttree_v2
python run_pipeline.py --sample-size 100
```

## Usage

### Core GraphRAG Interface
1. Open the web interface in your browser
2. Enter patient context (optional) in the sidebar
3. Submit a medical query such as:
   - "What are typical lab patterns for patients with high creatinine?"
   - "What medication combinations are used for urology patients?"
   - "Show cases with similar admission patterns"
4. Compare results across the three analysis approaches
5. Expand "Case Details" to see the underlying data used for analysis

### UTTree V2 Patient Similarity Pipeline
1. **Data Processing**: Extract and process MIMIC-III data for temporal analysis
   ```bash
   cd uttree_v2
   python run_pipeline.py --min-notes 10 --sample-size 1000
   ```

2. **Similarity Analysis**: Generate patient embeddings and store in Weaviate
   - Processes clinical notes with advanced NLP
   - Constructs temporal trees following UTTree methodology
   - Creates embeddings using mxbai-embed-large
   - Links vectors to Neo4j for GraphRAG integration

3. **Real-time Similarity Search**: Find similar patients for any admission
   ```python
   from uttree_v2.analysis import UTTreeAnalyzer
   analyzer = UTTreeAnalyzer()
   similar_patients = analyzer.find_similar_patients(hadm_id=12345, limit=10)
   ```

4. **GraphRAG Enhancement**: Use similarity data in medical queries
   - Vector embeddings enhance case retrieval
   - Temporal patterns improve medical reasoning
   - Hybrid graph-vector queries for comprehensive analysis

## Architecture

### Core GraphRAG System
- **Main App**: `app.py` - Streamlit web interface
- **GraphRAG Engine**: `components/graphrag.py` - Core RAG implementations
- **Configuration**: `util/config.py` - Settings management
- **Data Processing**: `vgsimi/` - Neo4j data loading scripts
- **Additional Pages**: `pages/` - Extra Streamlit functionality

### UTTree V2 Pipeline
- **UTTree Implementation**: `uttree/` - Original UTTree methodology with comprehensive documentation
- **Modern Pipeline**: `uttree_v2/` - Optimized implementation with advanced features
  - `1_data_preprocessing.py` - MIMIC-III data selection and structured processing
  - `2_nlp_processing.py` - Clinical NLP with ScispaCy and UMLS mapping
  - `3_tree_embedding.py` - Temporal tree construction and mxbai-embed-large embeddings
  - `4_vector_storage.py` - Weaviate integration and Neo4j linking
  - `5_analysis.py` - Advanced similarity analysis and clustering
  - `run_pipeline.py` - Complete pipeline orchestration

### Data Flow
```
MIMIC-III Data → UTTree Processing → Vector Embeddings → Weaviate Storage
                                                              ↓
Neo4j Graph ← GraphRAG Queries ← Hybrid Retrieval ← Similarity Search
```

## Contributing

This project works with sensitive medical data. Ensure compliance with data protection regulations when contributing.