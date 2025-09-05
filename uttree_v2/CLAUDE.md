# UTTree V2 Pipeline - CLAUDE.md

This directory contains the modernized UTTree V2 implementation with advanced embeddings, vector storage, and GraphRAG integration for patient similarity assessment.

## Project Overview

UTTree V2 is a next-generation implementation of the UTTree (Unstructured Temporal Tree) methodology, featuring modern embedding models, scalable vector storage, and seamless integration with GraphRAG systems.

## Research Foundation

Based on:
**"A study into patient similarity through representation learning from medical records"**  
by Memarzadeh, H., Ghadiri, N., Samwald, M., & Lotfi Shahreza, M. (2022)  
Knowledge and Information Systems, 64(12), 3293-3324.

## Key Improvements in V2

### Modern Technology Stack
- **mxbai-embed-large** via Ollama instead of Doc2Vec for superior embeddings
- **Weaviate vector database** for scalable similarity search
- **Environment-based configuration** (.env files)
- **Streamlined pipeline** with reduced intermediate storage

### Enhanced Architecture
- **In-memory processing** minimizes disk I/O
- **Modular design** with clear separation of concerns
- **GraphRAG integration** for hybrid medical queries
- **Real-time similarity search** capabilities

### Scalability Features
- **Vector database storage** supports millions of patients
- **Distributed processing** capabilities
- **API-ready architecture** for production deployment
- **Advanced clustering and analysis** tools

## Pipeline Architecture

### Module 1: Data Preprocessing (`1_data_preprocessing.py`)
**Optimized data selection and structured data processing**

Key Features:
- Combined patient selection and sampling
- In-memory prescription and lab processing
- Direct quadruple generation
- Quality filtering and validation

Functions:
- `load_and_filter_patients()`: Patient selection with documentation criteria
- `process_prescriptions()`: Drug data to temporal quadruples
- `process_lab_events()`: Laboratory data processing
- `combine_structured_data()`: Unified structured dataset creation

### Module 2: NLP Processing (`2_nlp_processing.py`)
**Integrated clinical NLP with direct quadruple output**

Key Features:
- Combined sectioning, NER, and UMLS mapping
- Direct quadruple generation without intermediate files
- Optimized NLP pipeline setup
- Memory-efficient processing

Functions:
- `process_clinical_notes()`: Complete NLP pipeline execution
- `_section_text()`: MedspaCy-based clinical note sectioning
- `_extract_concepts_from_section()`: ScispaCy NER and UMLS linking
- `generate_unstructured_quadruples()`: Direct quadruple conversion
- `integrate_structured_unstructured()`: Data integration by admission

### Module 3: Tree Construction and Embedding (`3_tree_embedding.py`)
**Modern embedding generation with mxbai-embed-large**

Key Features:
- Temporal tree construction following UTTree methodology
- Weisfeiler-Lehman relabeling algorithm
- BFS traversal sequence generation
- mxbai-embed-large embeddings via Ollama

Functions:
- `construct_temporal_tree()`: Four-level tree creation
- `apply_weisfeiler_lehman_relabeling()`: Graph kernel relabeling
- `generate_bfs_sequence()`: Sequence extraction for embedding
- `get_embedding_from_ollama()`: Modern embedding generation
- `process_admission_to_embedding()`: Complete tree-to-embedding pipeline

### Module 4: Vector Storage (`4_vector_storage.py`)
**Weaviate integration and Neo4j linking**

Key Features:
- Weaviate schema creation and management
- Scalable vector storage with metadata
- Neo4j admission linking for GraphRAG
- Automated similarity search setup

Functions:
- `create_uttree_schema()`: Weaviate schema initialization
- `store_embeddings_in_weaviate()`: Vector storage with metadata
- `link_admissions_to_vectors()`: Neo4j integration
- `test_similarity_search()`: Similarity search validation

### Module 5: Analysis (`5_analysis.py`)
**Advanced analysis and GraphRAG integration**

Key Features:
- Real-time vector similarity search
- Advanced clustering analysis
- GraphRAG integration testing
- Comprehensive reporting

Functions:
- `find_similar_patients()`: Weaviate-powered similarity search
- `perform_clustering_analysis()`: K-means and hierarchical clustering
- `test_graphrag_integration()`: Hybrid graph-vector queries
- `generate_analysis_report()`: Comprehensive evaluation

### Pipeline Runner (`run_pipeline.py`)
**Complete pipeline execution with command-line interface**

Features:
- End-to-end pipeline orchestration
- Command-line argument support
- Error handling and logging
- Analysis-only mode for evaluation

## Environment Configuration

### Required Environment Variables (.env)
```bash
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=mxbai-embed-large

# Weaviate Configuration  
WEAVIATE_URL=http://localhost:8080

# Additional configurations can be added as needed
```

### AppSettings.json Requirements
```json
{
    "neo4j": {
        "uri": "neo4j+s://your-instance.databases.neo4j.io",
        "user": "neo4j",
        "password": "your_password"
    },
    "directories": {
        "input_dir": "path/to/mimic/data",
        "def_dir": "path/to/mimic/definitions"
    }
}
```

## Dependencies

### Core Libraries
```bash
# Data Processing
pandas>=1.5.0
numpy>=1.24.0

# NLP Libraries
spacy>=3.4.0
medspacy>=1.2.0
scispacy>=0.5.0
negspacy>=1.0.0

# Graph Processing
networkx>=2.8.0

# Database Clients
weaviate-client>=3.15.0
neo4j>=5.0.0

# Machine Learning
scikit-learn>=1.2.0
matplotlib>=3.6.0
seaborn>=0.12.0
scipy>=1.10.0

# Utilities
python-dotenv>=0.19.0
requests>=2.28.0
```

### External Services
- **Ollama server** with mxbai-embed-large model
- **Weaviate database** for vector storage
- **Neo4j database** with MIMIC-III data

## Usage

### Quick Start
```bash
# Run complete pipeline with sample data
python run_pipeline.py --sample-size 10 --min-notes 5

# Run with all available patients
python run_pipeline.py --min-notes 10

# Analysis only (skip data processing)
python run_pipeline.py --analysis-only
```

### Individual Module Usage
```python
# Data preprocessing only
from data_preprocessing import UTTreeDataPreprocessor
preprocessor = UTTreeDataPreprocessor()
patients, structured_data = preprocessor.process_all(sample_size=50)

# NLP processing
from nlp_processing import UTTreeNLPProcessor
nlp_processor = UTTreeNLPProcessor()
integrated_data = nlp_processor.process_all(patients, structured_data)

# Embedding generation
from tree_embedding import UTTreeEmbeddingProcessor
embedding_processor = UTTreeEmbeddingProcessor()
results = embedding_processor.process_all_admissions(integrated_data)
```

### Analysis and Similarity Search
```python
from analysis import UTTreeAnalyzer
analyzer = UTTreeAnalyzer()

# Find similar patients
similar = analyzer.find_similar_patients(query_hadm_id=12345, limit=10)

# Generate comprehensive report
report = analyzer.generate_analysis_report("output_directory")
```

## Data Flow

### Processing Pipeline
1. **Patient Selection** → Filter MIMIC-III data for patients with adequate documentation
2. **Structured Processing** → Convert prescriptions/labs to temporal quadruples
3. **NLP Processing** → Extract medical concepts from clinical notes
4. **Data Integration** → Combine structured and unstructured quadruples by admission
5. **Tree Construction** → Build temporal trees with Weisfeiler-Lehman relabeling
6. **Sequence Generation** → Create BFS traversal sequences
7. **Embedding Generation** → Generate vectors using mxbai-embed-large
8. **Vector Storage** → Store in Weaviate with metadata
9. **Neo4j Linking** → Connect embeddings to graph database
10. **Analysis** → Clustering, similarity search, and evaluation

### Temporal Tree Structure
```
Level 1: Patient ID (Root)
    ├── Level 2: Time Window 1
    │   ├── Level 3: Retrospective Events
    │   │   └── Level 4: Past medical history concepts
    │   ├── Level 3: New Finding Events  
    │   │   └── Level 4: Current disease findings
    │   └── Level 3: Real-time Events
    │       └── Level 4: Medications, lab results
    └── Level 2: Time Window 2
        └── ... (similar structure)
```

## Integration with GenSimi GraphRAG

### Neo4j Integration
UTTree V2 enhances Neo4j admission nodes with:
- `uttree_vector_id`: Weaviate UUID for vector lookup
- `uttree_embedding_model`: Model used for embedding generation
- `uttree_updated_at`: Timestamp of last embedding update

### GraphRAG Query Support
```cypher
// Find admissions with similar temporal patterns
MATCH (a:Admission {hadm_id: $target_hadm_id})
WHERE a.uttree_vector_id IS NOT NULL
// Use vector similarity search in Weaviate
// Then enhance with graph relationships
MATCH (similar:Admission)-[:HAS_LAB]->(lab:LabEvent)
WHERE similar.hadm_id IN $similar_hadm_ids
RETURN similar, collect(lab) as labs
```

### Hybrid Retrieval
The system supports hybrid queries combining:
- **Vector similarity** from Weaviate for temporal pattern matching
- **Graph relationships** from Neo4j for medical context
- **Semantic search** for clinical concept matching

## Performance Characteristics

### Scalability
- **Weaviate storage**: Supports millions of patient embeddings
- **Similarity search**: Sub-second response for k-NN queries
- **Memory efficiency**: In-memory processing reduces I/O overhead
- **Parallel processing**: Module design supports distributed execution

### Quality Improvements
- **mxbai-embed-large**: Superior embeddings compared to Doc2Vec
- **Advanced NLP**: Latest ScispaCy models for medical text
- **Graph integration**: Enhanced context through medical knowledge graphs
- **Real-time analysis**: Dynamic similarity assessment capabilities

## Monitoring and Evaluation

### Built-in Metrics
- **Clustering quality**: Silhouette scores and Calinski-Harabasz index
- **Embedding statistics**: Dimensionality and distribution analysis
- **Similarity patterns**: Patient cohort analysis
- **GraphRAG integration**: Hybrid query performance

### Output Analysis
- **Dendrograms**: Hierarchical patient similarity visualization
- **Cluster analysis**: Patient group identification
- **Similarity matrices**: Detailed patient comparison results
- **Performance reports**: Processing time and success rate metrics

## Troubleshooting

### Common Issues
1. **Ollama connection**: Ensure mxbai-embed-large model is available
2. **Weaviate setup**: Verify database is running and accessible
3. **Neo4j integration**: Check credentials and network connectivity
4. **Memory requirements**: Large datasets may require increased RAM
5. **NLP models**: Ensure ScispaCy models are properly installed

### Performance Optimization
- **Batch processing**: Process patients in smaller batches for memory efficiency
- **Model caching**: Keep NLP models loaded for repeated runs
- **Database indexing**: Ensure proper Neo4j and Weaviate indices
- **Parallel execution**: Use multiple workers for embedding generation

## Future Enhancements

### Planned Features
- **Multi-modal embeddings**: Integration of imaging and genomic data
- **Federated learning**: Privacy-preserving multi-site analysis
- **Real-time streaming**: Live patient similarity assessment
- **Advanced visualizations**: Interactive patient similarity exploration

### Research Extensions
- **UTTree-H implementation**: Historical context integration
- **Attention mechanisms**: Focus on clinically relevant patterns
- **Explainable similarity**: Interpretable patient comparison features
- **Clinical validation**: Evaluation with clinical outcomes data

## Contributing

When extending UTTree V2:
1. Follow the modular architecture pattern
2. Maintain environment-based configuration
3. Include comprehensive error handling
4. Add unit tests for new functionality
5. Update documentation and examples

This modernized implementation provides a solid foundation for advanced patient similarity research while maintaining compatibility with the GenSimi GraphRAG ecosystem.