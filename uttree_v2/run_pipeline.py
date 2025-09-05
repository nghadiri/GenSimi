"""
UTTree V2 - Complete Pipeline Runner

Execute the complete UTTree V2 pipeline from data preprocessing to analysis,
with modern embeddings, vector storage, and GraphRAG integration.

Usage:
    python run_pipeline.py [--sample-size N] [--min-notes N] [--analysis-only]
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Optional

# Import all pipeline modules
from data_preprocessing import UTTreeDataPreprocessor
from nlp_processing import UTTreeNLPProcessor
from tree_embedding import UTTreeEmbeddingProcessor
from vector_storage import UTTreeVectorStorage
from analysis import UTTreeAnalyzer

def run_complete_pipeline(sample_size: Optional[int] = None, 
                         min_notes: int = 10,
                         analysis_only: bool = False):
    """
    Execute the complete UTTree V2 pipeline.
    
    Args:
        sample_size: Optional sample size for testing (None = all patients)
        min_notes: Minimum notes per patient
        analysis_only: If True, skip data processing and run analysis only
    """
    start_time = datetime.now()
    print("="*60)
    print("UTTree V2 - Complete Pipeline Execution")
    print("="*60)
    print(f"Start time: {start_time}")
    print(f"Sample size: {sample_size if sample_size else 'All patients'}")
    print(f"Min notes per patient: {min_notes}")
    print(f"Analysis only: {analysis_only}")
    print()
    
    try:
        if not analysis_only:
            # Phase 1: Data Preprocessing
            print("Phase 1: Data Preprocessing")
            print("-" * 30)
            preprocessor = UTTreeDataPreprocessor()
            selected_patients, structured_data = preprocessor.process_all(
                min_notes=min_notes, 
                sample_size=sample_size
            )
            print(f"✓ Selected {len(selected_patients)} patients")
            print(f"✓ Generated {len(structured_data)} structured data records")
            print()
            
            # Phase 2: NLP Processing
            print("Phase 2: NLP Processing")
            print("-" * 30)
            nlp_processor = UTTreeNLPProcessor()
            integrated_data = nlp_processor.process_all(selected_patients, structured_data)
            print(f"✓ Processed {len(integrated_data)} admissions with NLP")
            print()
            
            # Phase 3: Tree Construction and Embedding
            print("Phase 3: Tree Construction and Embedding")
            print("-" * 30)
            embedding_processor = UTTreeEmbeddingProcessor()
            embedding_results = embedding_processor.process_all_admissions(integrated_data)
            
            successful_embeddings = sum(1 for _, _, emb in embedding_results if emb is not None)
            print(f"✓ Generated {successful_embeddings} embeddings")
            print()
            
            # Phase 4: Vector Storage and Neo4j Linking
            print("Phase 4: Vector Storage and Neo4j Linking")
            print("-" * 30)
            vector_storage = UTTreeVectorStorage()
            vector_storage.process_and_store_all(embedding_results)
            print("✓ Stored embeddings in Weaviate and linked to Neo4j")
            print()
            
            # Clean up connections
            vector_storage.close_connections()
        
        # Phase 5: Analysis and Evaluation
        print("Phase 5: Analysis and Evaluation")
        print("-" * 30)
        analyzer = UTTreeAnalyzer()
        
        # Create analysis output directory
        analysis_dir = os.path.join(os.getcwd(), f"uttree_v2_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Generate comprehensive analysis report
        report = analyzer.generate_analysis_report(analysis_dir)
        
        print("✓ Analysis completed")
        print(f"✓ Results saved to: {analysis_dir}")
        
        # Display summary
        if "error" not in report:
            stats = report.get("embedding_statistics", {})
            print(f"✓ Total embeddings analyzed: {stats.get('total_embeddings', 0)}")
            
            clustering = report.get("clustering_results", {})
            if clustering:
                kmeans_score = clustering.get("kmeans", {}).get("silhouette_score", 0)
                print(f"✓ Clustering silhouette score: {kmeans_score:.3f}")
        
        # Clean up connections
        analyzer.close_connections()
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print()
        print("="*60)
        print("Pipeline Execution Summary")
        print("="*60)
        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Total duration: {duration}")
        print(f"Status: SUCCESS")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(
        description="Execute UTTree V2 pipeline for patient similarity analysis"
    )
    
    parser.add_argument(
        "--sample-size", 
        type=int, 
        help="Number of patients to sample for processing (default: all)"
    )
    
    parser.add_argument(
        "--min-notes", 
        type=int, 
        default=10,
        help="Minimum number of clinical notes per patient (default: 10)"
    )
    
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Skip data processing and run analysis only"
    )
    
    args = parser.parse_args()
    
    # Execute pipeline
    run_complete_pipeline(
        sample_size=args.sample_size,
        min_notes=args.min_notes,
        analysis_only=args.analysis_only
    )

if __name__ == "__main__":
    main()