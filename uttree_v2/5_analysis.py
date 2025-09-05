"""
UTTree V2 - Analysis and Similarity Assessment Module

Modern analysis tools for evaluating UTTree embeddings using Weaviate similarity search,
cluster analysis, and integration with GraphRAG queries.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Improvements in V2:
- Weaviate-powered similarity search instead of cosine matrices
- Real-time patient similarity assessment
- GraphRAG integration for hybrid medical queries
- Advanced clustering and evaluation metrics

Analysis Features:
1. Vector Similarity Search and Evaluation
2. Patient Clustering Analysis
3. GraphRAG Query Integration
4. Performance Metrics and Visualization
"""

import weaviate
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from scipy.cluster.hierarchy import dendrogram, linkage
import os
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings

class UTTreeAnalyzer:
    def __init__(self):
        self.settings = load_app_settings()
        
        # Get configuration from environment
        self.weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        self.neo4j_uri = self.settings['neo4j']['uri']
        self.neo4j_user = self.settings['neo4j']['user']
        self.neo4j_password = self.settings['neo4j']['password']
        
        # Initialize connections
        self.weaviate_client = None
        self.neo4j_driver = None
        
        self._setup_connections()
    
    def _setup_connections(self):
        """Initialize Weaviate and Neo4j connections."""
        try:
            # Initialize Weaviate client
            self.weaviate_client = weaviate.Client(url=self.weaviate_url)
            
            if self.weaviate_client.is_ready():
                print("Connected to Weaviate for analysis")
            else:
                print("Warning: Could not connect to Weaviate")
                
            # Initialize Neo4j driver
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            print("Connected to Neo4j for analysis")
                    
        except Exception as e:
            print(f"Error setting up analysis connections: {e}")
    
    def get_all_embeddings(self) -> Tuple[List[Dict], np.ndarray]:
        """
        Retrieve all UTTree embeddings from Weaviate.
        
        Returns:
            Tuple of (metadata_list, embedding_matrix)
        """
        print("Retrieving all embeddings from Weaviate...")
        
        try:
            result = (
                self.weaviate_client
                .query
                .get("UTTreeEmbedding", [
                    "hadm_id", "subject_id", "temporal_sequence", 
                    "sequence_length", "medical_events_count", "created_at"
                ])
                .with_additional(["vector"])
                .with_limit(10000)  # Adjust based on your data size
                .do()
            )
            
            embeddings_data = result["data"]["Get"]["UTTreeEmbedding"]
            
            if not embeddings_data:
                print("No embeddings found in Weaviate")
                return [], np.array([])
            
            # Extract metadata and vectors
            metadata = []
            vectors = []
            
            for item in embeddings_data:
                metadata.append({
                    'hadm_id': item['hadm_id'],
                    'subject_id': item['subject_id'],
                    'sequence_length': item['sequence_length'],
                    'medical_events_count': item['medical_events_count'],
                    'created_at': item['created_at']
                })
                vectors.append(item['_additional']['vector'])
            
            embedding_matrix = np.array(vectors)
            
            print(f"Retrieved {len(metadata)} embeddings with {embedding_matrix.shape[1]} dimensions")
            return metadata, embedding_matrix
            
        except Exception as e:
            print(f"Error retrieving embeddings: {e}")
            return [], np.array([])
    
    def find_similar_patients(self, query_hadm_id: int, limit: int = 10) -> List[Dict]:
        """
        Find patients similar to a query patient using Weaviate similarity search.
        
        Args:
            query_hadm_id: HADM_ID to find similar patients for
            limit: Number of similar patients to return
            
        Returns:
            List of similar patient dictionaries with metadata
        """
        print(f"Finding similar patients to HADM_ID {query_hadm_id}...")
        
        try:
            # Get the query embedding
            query_result = (
                self.weaviate_client
                .query
                .get("UTTreeEmbedding", ["hadm_id"])
                .with_where({
                    "path": ["hadm_id"],
                    "operator": "Equal",
                    "valueInt": query_hadm_id
                })
                .with_additional(["vector"])
                .do()
            )
            
            if not query_result["data"]["Get"]["UTTreeEmbedding"]:
                print(f"No embedding found for HADM_ID {query_hadm_id}")
                return []
            
            query_vector = query_result["data"]["Get"]["UTTreeEmbedding"][0]["_additional"]["vector"]
            
            # Perform similarity search
            similar_results = (
                self.weaviate_client
                .query
                .get("UTTreeEmbedding", [
                    "hadm_id", "subject_id", "sequence_length", 
                    "medical_events_count", "temporal_sequence"
                ])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit + 1)  # +1 to exclude self
                .with_additional(["distance", "certainty"])
                .do()
            )
            
            # Process results and exclude the query patient
            similar_patients = []
            for result in similar_results["data"]["Get"]["UTTreeEmbedding"]:
                if result["hadm_id"] != query_hadm_id:
                    similar_patients.append({
                        "hadm_id": result["hadm_id"],
                        "subject_id": result["subject_id"],
                        "distance": result["_additional"]["distance"],
                        "certainty": result["_additional"]["certainty"],
                        "sequence_length": result["sequence_length"],
                        "medical_events_count": result["medical_events_count"]
                    })
            
            return similar_patients[:limit]
            
        except Exception as e:
            print(f"Error finding similar patients: {e}")
            return []
    
    def perform_clustering_analysis(self, metadata: List[Dict], embeddings: np.ndarray, 
                                  output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform clustering analysis on UTTree embeddings.
        
        Args:
            metadata: List of metadata dictionaries
            embeddings: Embedding matrix
            output_dir: Directory to save visualizations
            
        Returns:
            Dictionary with clustering results and metrics
        """
        print("Performing clustering analysis...")
        
        if len(embeddings) == 0:
            print("No embeddings available for clustering")
            return {}
        
        # Standardize embeddings
        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)
        
        results = {}
        
        # K-means clustering
        print("Running K-means clustering...")
        n_clusters_range = range(2, min(10, len(embeddings) // 2))
        kmeans_scores = []
        
        for n_clusters in n_clusters_range:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings_scaled)
            
            silhouette_avg = silhouette_score(embeddings_scaled, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(embeddings_scaled, cluster_labels)
            
            kmeans_scores.append({
                'n_clusters': n_clusters,
                'silhouette_score': silhouette_avg,
                'calinski_harabasz_score': calinski_harabasz
            })
        
        # Find optimal number of clusters
        best_kmeans = max(kmeans_scores, key=lambda x: x['silhouette_score'])
        
        # Perform final K-means with optimal clusters
        final_kmeans = KMeans(n_clusters=best_kmeans['n_clusters'], random_state=42)
        kmeans_labels = final_kmeans.fit_predict(embeddings_scaled)
        
        results['kmeans'] = {
            'n_clusters': best_kmeans['n_clusters'],
            'labels': kmeans_labels.tolist(),
            'silhouette_score': best_kmeans['silhouette_score'],
            'scores_by_k': kmeans_scores
        }
        
        # Hierarchical clustering
        print("Running hierarchical clustering...")
        linkage_matrix = linkage(embeddings_scaled, method='ward')
        
        # Create dendrogram
        if output_dir:
            plt.figure(figsize=(15, 8))
            labels = [f"P{m['subject_id']}-A{m['hadm_id']}" for m in metadata]
            dendrogram(
                linkage_matrix,
                labels=labels,
                leaf_rotation=90,
                leaf_font_size=8
            )
            plt.title('UTTree Patient Similarity Dendrogram')
            plt.xlabel('Patient-Admission ID')
            plt.ylabel('Distance')
            plt.tight_layout()
            
            dendrogram_path = os.path.join(output_dir, 'uttree_v2_dendrogram.png')
            plt.savefig(dendrogram_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Dendrogram saved to {dendrogram_path}")
        
        # Hierarchical clustering with optimal number of clusters
        hierarchical = AgglomerativeClustering(n_clusters=best_kmeans['n_clusters'])
        hierarchical_labels = hierarchical.fit_predict(embeddings_scaled)
        
        hierarchical_silhouette = silhouette_score(embeddings_scaled, hierarchical_labels)
        
        results['hierarchical'] = {
            'n_clusters': best_kmeans['n_clusters'],
            'labels': hierarchical_labels.tolist(),
            'silhouette_score': hierarchical_silhouette,
            'linkage_matrix': linkage_matrix.tolist()
        }
        
        print(f"Clustering completed - K-means silhouette: {best_kmeans['silhouette_score']:.3f}, "
              f"Hierarchical silhouette: {hierarchical_silhouette:.3f}")
        
        return results
    
    def analyze_patient_similarity_patterns(self, metadata: List[Dict]) -> Dict[str, Any]:
        """
        Analyze patterns in patient similarity based on metadata.
        
        Args:
            metadata: List of metadata dictionaries
            
        Returns:
            Dictionary with pattern analysis results
        """
        print("Analyzing patient similarity patterns...")
        
        if not metadata:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(metadata)
        
        patterns = {
            'total_patients': len(df),
            'unique_subjects': df['subject_id'].nunique(),
            'sequence_length_stats': {
                'mean': df['sequence_length'].mean(),
                'std': df['sequence_length'].std(),
                'min': df['sequence_length'].min(),
                'max': df['sequence_length'].max()
            },
            'medical_events_stats': {
                'mean': df['medical_events_count'].mean(),
                'std': df['medical_events_count'].std(),
                'min': df['medical_events_count'].min(),
                'max': df['medical_events_count'].max()
            }
        }
        
        # Correlation analysis
        numeric_cols = ['sequence_length', 'medical_events_count']
        if len(numeric_cols) > 1:
            correlation_matrix = df[numeric_cols].corr()
            patterns['correlations'] = correlation_matrix.to_dict()
        
        return patterns
    
    def test_graphrag_integration(self, test_hadm_id: int) -> Dict[str, Any]:
        """
        Test integration with GraphRAG by combining vector similarity and graph queries.
        
        Args:
            test_hadm_id: HADM_ID to test GraphRAG integration
            
        Returns:
            Dictionary with GraphRAG test results
        """
        print(f"Testing GraphRAG integration for HADM_ID {test_hadm_id}...")
        
        try:
            # Step 1: Find similar patients using vector search
            similar_patients = self.find_similar_patients(test_hadm_id, limit=5)
            
            if not similar_patients:
                return {"error": "No similar patients found"}
            
            # Step 2: Get graph-based information for similar patients
            similar_hadm_ids = [p['hadm_id'] for p in similar_patients]
            
            with self.neo4j_driver.session() as session:
                # Get medical information for similar patients
                graph_info_query = """
                MATCH (a:Admission)
                WHERE a.hadm_id IN $hadm_ids
                OPTIONAL MATCH (a)-[:HAS_LAB]->(lab:LabEvent)
                OPTIONAL MATCH (a)-[:HAS_PRESCRIPTION]->(rx:Prescription)
                OPTIONAL MATCH (a)-[:HAS_NOTE]->(note:NoteEvent)
                RETURN a.hadm_id as hadm_id,
                       count(DISTINCT lab) as lab_count,
                       count(DISTINCT rx) as prescription_count,
                       count(DISTINCT note) as note_count
                ORDER BY a.hadm_id
                """
                
                result = session.run(graph_info_query, hadm_ids=similar_hadm_ids)
                graph_data = [dict(record) for record in result]
            
            # Combine vector similarity with graph data
            integrated_results = []
            for i, similar_patient in enumerate(similar_patients):
                # Find corresponding graph data
                graph_match = next(
                    (g for g in graph_data if g['hadm_id'] == similar_patient['hadm_id']), 
                    {}
                )
                
                integrated_results.append({
                    **similar_patient,
                    **graph_match
                })
            
            return {
                "test_hadm_id": test_hadm_id,
                "similar_patients_with_graph_data": integrated_results,
                "integration_success": True
            }
            
        except Exception as e:
            print(f"Error in GraphRAG integration test: {e}")
            return {"error": str(e), "integration_success": False}
    
    def generate_analysis_report(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report of UTTree V2 embeddings.
        
        Args:
            output_dir: Directory to save analysis outputs
            
        Returns:
            Dictionary with complete analysis results
        """
        print("Generating comprehensive analysis report...")
        
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "uttree_version": "v2",
            "embedding_model": "mxbai-embed-large"
        }
        
        # Get all embeddings
        metadata, embeddings = self.get_all_embeddings()
        
        if len(embeddings) == 0:
            report["error"] = "No embeddings found for analysis"
            return report
        
        # Basic statistics
        report["embedding_statistics"] = {
            "total_embeddings": len(embeddings),
            "embedding_dimensions": embeddings.shape[1],
            "unique_subjects": len(set(m['subject_id'] for m in metadata))
        }
        
        # Pattern analysis
        report["similarity_patterns"] = self.analyze_patient_similarity_patterns(metadata)
        
        # Clustering analysis
        report["clustering_results"] = self.perform_clustering_analysis(
            metadata, embeddings, output_dir
        )
        
        # Test similarity search with first available admission
        if metadata:
            test_hadm_id = metadata[0]['hadm_id']
            
            # Similarity search test
            similar_patients = self.find_similar_patients(test_hadm_id, limit=5)
            report["similarity_search_test"] = {
                "query_hadm_id": test_hadm_id,
                "similar_patients": similar_patients
            }
            
            # GraphRAG integration test
            report["graphrag_integration_test"] = self.test_graphrag_integration(test_hadm_id)
        
        # Save report if output directory specified
        if output_dir:
            report_path = os.path.join(output_dir, 'uttree_v2_analysis_report.json')
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Analysis report saved to {report_path}")
        
        return report
    
    def close_connections(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        print("Analysis connections closed")


def main():
    """Main execution function for analysis."""
    analyzer = UTTreeAnalyzer()
    
    try:
        # Set output directory for analysis results
        output_dir = os.path.join(os.getcwd(), "uttree_v2_analysis")
        
        # Generate comprehensive analysis report
        report = analyzer.generate_analysis_report(output_dir)
        
        # Display key results
        print("\n" + "="*50)
        print("UTTree V2 Analysis Summary")
        print("="*50)
        
        if "error" in report:
            print(f"Analysis Error: {report['error']}")
            return
        
        stats = report.get("embedding_statistics", {})
        print(f"Total Embeddings: {stats.get('total_embeddings', 0)}")
        print(f"Embedding Dimensions: {stats.get('embedding_dimensions', 0)}")
        print(f"Unique Subjects: {stats.get('unique_subjects', 0)}")
        
        # Clustering results
        clustering = report.get("clustering_results", {})
        if clustering:
            kmeans_score = clustering.get("kmeans", {}).get("silhouette_score", 0)
            hierarchical_score = clustering.get("hierarchical", {}).get("silhouette_score", 0)
            print(f"K-means Silhouette Score: {kmeans_score:.3f}")
            print(f"Hierarchical Silhouette Score: {hierarchical_score:.3f}")
        
        # GraphRAG integration test
        graphrag_test = report.get("graphrag_integration_test", {})
        if graphrag_test.get("integration_success"):
            similar_count = len(graphrag_test.get("similar_patients_with_graph_data", []))
            print(f"GraphRAG Integration: Success ({similar_count} similar patients found)")
        else:
            print("GraphRAG Integration: Failed")
        
        print(f"\nDetailed results saved to: {output_dir}")
        
    except Exception as e:
        print(f"Error in analysis execution: {e}")
    finally:
        analyzer.close_connections()


if __name__ == "__main__":
    main()