# UTTree Pipeline - CLAUDE.md

This directory implements the UTTree (Unstructured Temporal Tree) methodology for patient similarity assessment, based on the research from HodaMemar/Patient-Similarity-through-Representation.

## Project Overview

The UTTree methodology combines structured and unstructured EMR data using temporal tree structures to create patient representations for similarity assessment. This implementation processes MIMIC-III data through a complete pipeline from data selection to similarity calculation.

## Research Foundation

Based on:
**"A study into patient similarity through representation learning from medical records"**  
by Memarzadeh, H., Ghadiri, N., Samwald, M., & Lotfi Shahreza, M. (2022)  
Knowledge and Information Systems, 64(12), 3293-3324.

The methodology addresses patient similarity assessment by:
- Converting heterogeneous EMRs into comparable formats
- Using unsupervised methods to build patient representations
- Integrating unstructured and structured EMR data
- Employing tree structures to model temporal medical events
- Extracting medical concepts using MedspaCy and ScispaCy
- Mapping entities to UMLS (Unified Medical Language System)

## Pipeline Architecture

### Phase 1: Data Preprocessing (Files 0-2)

**0 select.py** - Data Selection Module
- Filters MIMIC-III dataset files for selected patients
- Processes: PATIENTS, ADMISSIONS, LABEVENTS, NOTEEVENTS, PRESCRIPTIONS, PROCEDURES_ICD, DIAGNOSES_ICD
- Creates manageable datasets while preserving all related medical events

**0_my_sampling.py** - Patient Sampling Module
- Analyzes patient admission and clinical note distributions
- Filters patients with minimum clinical documentation (≥10 notes)
- Creates random samples for model development and testing
- Generates visualizations of data distributions

**1_my_struct.py** - Structured Data Processing
- Processes prescriptions and laboratory events into quadruple format
- Creates daily drug administration records with temporal sequences
- Maps lab results to quadruple structure: {time, event_type, entity, value}
- Assigns 'RealTime' temporal event type for short-term effects

**2_my_ner.py** - Named Entity Recognition
- Extracts medical concepts from clinical notes using NLP
- Uses MedspaCy for clinical note sectioning
- Applies ScispaCy (BC5CDR model) for medical NER
- Maps concepts to UMLS using MetaMap for standardization
- Assigns temporal roles: 'Retro' (past history) vs 'NewFinding' (current)

### Phase 2: Data Integration (Files 3a-3c)

**3a process_unstruct.py** - Unstructured Data Processor
- Converts NLP extraction results to quadruple format
- Groups by hospital admission (HADM_ID) with temporal ordering
- Maps clinical sections to temporal event types
- Outputs: {HADM_ID}-unst.csv files

**3b process_struct.py** - Structured Data Processor
- Processes merged drug and lab data to quadruple format
- Filters clinically significant events (drugs and abnormal labs)
- Maintains temporal ordering with 'RealTime' event classification
- Outputs: {HADM_ID}-st.csv files

**3c merge.py** - Data Integration Module
- Merges structured and unstructured quadruple files per admission
- Creates unified temporal datasets combining both data types
- Sorts by temporal sequence for tree construction
- Outputs: {HADM_ID}-merged.csv files

### Phase 3: Tree Construction and Representation (Files 4-5)

**4 createtree_relabeling.py** - Core UTTree Algorithm
- Creates four-level temporal trees: Patient → Time Windows → Event Types → Medical Events
- Applies Weisfeiler-Lehman relabeling algorithm
- Generates BFS traversal sequences capturing medical event co-occurrences
- Outputs: {HADM_ID}-merged.txt files with temporal tree sequences

**5 doc2vec.py** - Document Representation Integration
- Loads temporal tree sequences into Neo4j for GraphRAG integration
- Updates admission nodes with temporal_tree_string properties
- Prepares sequences for Doc2Vec processing
- Enables hybrid retrieval combining graph structure and temporal patterns

### Phase 4: Analysis and Evaluation (File 6+)

**6 cluster_adm.py** - Patient Clustering Analysis
- Performs K-means and hierarchical clustering on patient embeddings
- Generates dendrograms showing patient similarity relationships
- Validates UTTree representation quality through downstream tasks

**calculating_cosine_similarity.py** - Patient Similarity Assessment
- Calculates pairwise cosine similarity between patient embeddings
- Creates similarity matrices for patient comparison
- Core evaluation metric for UTTree methodology

**graph_sequence.py** - Alternative Graph Implementation
- Provides NetworkX-based alternative for sequence generation
- Experimental variations of core UTTree methodology
- Multiple document generation strategies for comparison

## Quadruple Data Structure

Central to the methodology is the quadruple format: **{t_i, y_i, e_i, v_i}**

- **Time (t_i)**: Timestamp of clinical event registration
- **Temporal Event Type (y_i)**: 
  - `Retrospective`: Past medical history concepts
  - `NewFinding`: Current visit diseases with long-lasting effects
  - `RealTime`: Short-term medical events (drugs, labs)
- **Event (e_i)**: Medical event type (disease, drug, lab, procedure)
- **Value (v_i)**: Medical event value or concept name

## Temporal Tree Structure

Four-level hierarchy:
1. **Level 1**: Patient identifier (root)
2. **Level 2**: Time windows (1-day subtrees)
3. **Level 3**: Temporal event types (Retro/NewFinding/RealTime branches)
4. **Level 4**: Medical events (leaf nodes with actual medical data)

## Key Dependencies

### NLP Libraries
- `medspacy`: Clinical text sectioning and preprocessing
- `scispacy`: Medical named entity recognition (BC5CDR model)
- `negspacy`: Negation detection in clinical text

### Data Processing
- `pandas`: Data manipulation and CSV processing
- `networkx`: Graph operations and BFS traversal

### Machine Learning
- `sklearn`: Clustering algorithms and similarity metrics
- `gensim`: Doc2Vec implementation (external to this pipeline)

### Graph Database
- `neo4j`: Graph database integration for GraphRAG

## Usage Workflow

1. **Data Selection**: Run `0 select.py` to filter MIMIC-III data
2. **Sampling**: Execute `0_my_sampling.py` for patient filtering
3. **Structured Processing**: Run `1_my_struct.py` for drugs and labs
4. **NLP Processing**: Execute `2_my_ner.py` for clinical note concepts
5. **Data Integration**: Run `3a`, `3b`, `3c` modules in sequence
6. **Tree Construction**: Execute `4 createtree_relabeling.py`
7. **GraphRAG Integration**: Run `5 doc2vec.py` to load into Neo4j
8. **Analysis**: Use `6 cluster_adm.py` and similarity modules for evaluation

## Integration with GenSimi GraphRAG

This UTTree implementation extends the original patient similarity work by:
- Creating temporal tree strings stored in Neo4j admission nodes
- Enabling GraphRAG queries to utilize temporal patient patterns
- Supporting hybrid retrieval combining graph relationships and similarity
- Providing rich patient representations for medical case analysis

The temporal_tree_string property added to Neo4j admission nodes contains the BFS traversal sequences, enabling the GenSimi GraphRAG system to leverage both structured medical knowledge and temporal patient similarity patterns.

## Configuration

Uses the project's AppSettings.json configuration:
- Input/output directory settings
- Neo4j connection parameters
- Processing parameters and file paths

Ensure proper directory structure:
```
input_dir/
├── MIMIC-III CSV files
├── proc/ (intermediate processing files)
└── proc/merged/ (final merged data)
```

## Important Notes

- Processes medical data requiring careful handling and compliance
- Temporal sequences capture both medical event co-occurrences and time relationships
- Weisfeiler-Lehman relabeling enables comparison of complex medical patterns
- Integration with GraphRAG enables advanced medical case analysis and retrieval