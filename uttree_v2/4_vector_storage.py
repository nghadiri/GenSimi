"""
UTTree V2 - Weaviate Vector Storage and Neo4j Integration Module

Modern vector storage using Weaviate for embeddings with Neo4j linking,
replacing traditional similarity matrices with scalable vector database.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Improvements in V2:
- Weaviate vector database for scalable similarity search
- Neo4j integration for graph-vector hybrid queries
- Environment-based configuration (.env)
- Automated schema creation and data ingestion

Processing Steps:
1. Weaviate Schema Creation and Management
2. Vector Storage with Metadata
3. Neo4j Admission Linking
4. Hybrid Query Support Infrastructure
"""

import weaviate
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
import json
from datetime import datetime
import sys
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Add parent directory to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings

class UTTreeVectorStorage:
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
            
            # Test Weaviate connection
            if self.weaviate_client.is_ready():
                print("Connected to Weaviate successfully")
            else:
                print("Warning: Could not connect to Weaviate")
                
            # Initialize Neo4j driver
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single():
                    print("Connected to Neo4j successfully")
                    
        except Exception as e:
            print(f"Error setting up connections: {e}")
    
    def create_uttree_schema(self):
        """
        Create Weaviate schema for UTTree patient embeddings.
        """
        try:
            # Define the UTTree schema
            uttree_schema = {
                "class": "UTTreeEmbedding",
                "description": "Patient temporal tree embeddings from UTTree methodology",
                "properties": [
                    {
                        "name": "hadm_id",
                        "dataType": ["int"],
                        "description": "Hospital admission ID"
                    },
                    {
                        "name": "subject_id",
                        "dataType": ["int"],
                        "description": "Patient subject ID"
                    },
                    {
                        "name": "temporal_sequence",
                        "dataType": ["text"],
                        "description": "BFS traversal sequence from temporal tree"
                    },
                    {
                        "name": "embedding_model",
                        "dataType": ["string"],
                        "description": "Model used for embedding generation"
                    },
                    {
                        "name": "created_at",
                        "dataType": ["date"],
                        "description": "Timestamp when embedding was created"
                    },
                    {
                        "name": "sequence_length",
                        "dataType": ["int"],
                        "description": "Length of the temporal sequence"
                    },
                    {
                        "name": "medical_events_count",
                        "dataType": ["int"],
                        "description": "Number of medical events in the temporal tree"
                    }
                ],
                "vectorizer": "none"  # We provide our own vectors
            }
            
            # Check if schema already exists
            existing_classes = self.weaviate_client.schema.get()["classes"]
            class_names = [cls["class"] for cls in existing_classes]
            
            if "UTTreeEmbedding" not in class_names:
                self.weaviate_client.schema.create_class(uttree_schema)
                print("Created UTTreeEmbedding schema in Weaviate")
            else:
                print("UTTreeEmbedding schema already exists")
                
        except Exception as e:
            print(f"Error creating Weaviate schema: {e}")
    
    def store_embeddings_in_weaviate(self, results: List[Tuple[int, str, Optional[List[float]]]]) -> Dict[int, str]:
        """
        Store UTTree embeddings in Weaviate with metadata.
        
        Args:
            results: List of tuples (hadm_id, sequence, embedding)
            
        Returns:
            Dictionary mapping hadm_id to Weaviate object UUID
        """
        print("Storing embeddings in Weaviate...")
        
        hadm_id_to_uuid = {}
        successful_stores = 0
        
        # Get subject_id mapping from Neo4j
        subject_id_mapping = self._get_subject_id_mapping()
        
        for hadm_id, sequence, embedding in results:
            if embedding is None:
                continue
                
            try:
                # Prepare metadata
                properties = {
                    "hadm_id": int(hadm_id),
                    "subject_id": int(subject_id_mapping.get(hadm_id, -1)),
                    "temporal_sequence": sequence,
                    "embedding_model": "mxbai-embed-large",
                    "created_at": datetime.now().isoformat() + "Z",
                    "sequence_length": len(sequence),
                    "medical_events_count": sequence.count("_")  # Rough estimate
                }
                
                # Store in Weaviate with embedding vector
                uuid_obj = self.weaviate_client.data_object.create(
                    data_object=properties,
                    class_name="UTTreeEmbedding",
                    vector=embedding
                )
                
                hadm_id_to_uuid[hadm_id] = uuid_obj
                successful_stores += 1
                
                if successful_stores % 10 == 0:
                    print(f"Stored {successful_stores} embeddings in Weaviate")
                    
            except Exception as e:
                print(f"Error storing embedding for HADM_ID {hadm_id}: {e}")
                continue
        
        print(f"Successfully stored {successful_stores} embeddings in Weaviate")
        return hadm_id_to_uuid
    
    def _get_subject_id_mapping(self) -> Dict[int, int]:
        """
        Get mapping of HADM_ID to SUBJECT_ID from Neo4j.
        
        Returns:
            Dictionary mapping hadm_id to subject_id
        """
        mapping = {}
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (a:Admission) 
                    WHERE a.hadm_id IS NOT NULL
                    RETURN a.hadm_id as hadm_id, a.subject_id as subject_id
                """)
                
                for record in result:
                    hadm_id = int(record["hadm_id"])
                    subject_id = int(record["subject_id"])
                    mapping[hadm_id] = subject_id
                    
        except Exception as e:
            print(f"Error getting subject_id mapping from Neo4j: {e}")
            
        return mapping
    
    def link_admissions_to_vectors(self, hadm_id_to_uuid: Dict[int, str]):
        """
        Add Weaviate UUID references to Neo4j admission nodes.
        
        Args:
            hadm_id_to_uuid: Dictionary mapping hadm_id to Weaviate UUID
        """
        print("Linking Neo4j admissions to Weaviate vectors...")
        
        successful_links = 0
        
        try:
            with self.neo4j_driver.session() as session:
                for hadm_id, weaviate_uuid in hadm_id_to_uuid.items():
                    try:
                        session.execute_write(
                            self._update_admission_with_vector_id,
                            hadm_id, weaviate_uuid
                        )
                        successful_links += 1
                        
                        if successful_links % 10 == 0:
                            print(f"Linked {successful_links} admissions to vectors")
                            
                    except Exception as e:
                        print(f"Error linking HADM_ID {hadm_id}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in Neo4j linking process: {e}")
            
        print(f"Successfully linked {successful_links} admissions to Weaviate vectors")
    
    @staticmethod
    def _update_admission_with_vector_id(tx, hadm_id: int, weaviate_uuid: str):
        """
        Update Neo4j admission node with Weaviate vector UUID.
        
        Args:
            tx: Neo4j transaction
            hadm_id: Hospital admission ID
            weaviate_uuid: Weaviate object UUID
        """
        query = """
        MATCH (a:Admission {hadm_id: $hadm_id})
        SET a.uttree_vector_id = $weaviate_uuid,
            a.uttree_embedding_model = 'mxbai-embed-large',
            a.uttree_updated_at = datetime()
        RETURN a.hadm_id as updated_hadm_id
        """
        
        result = tx.run(query, hadm_id=hadm_id, weaviate_uuid=weaviate_uuid)
        return result.single()
    
    def create_vector_similarity_index(self):
        """
        Create or update vector similarity search configuration in Weaviate.
        """
        try:
            # The schema creation with vectorizer: "none" allows us to provide our own vectors
            # Weaviate automatically creates HNSW index for similarity search
            print("Vector similarity index ready in Weaviate")
            
        except Exception as e:
            print(f"Error setting up vector similarity index: {e}")
    
    def test_similarity_search(self, test_hadm_id: int, limit: int = 5) -> List[Dict]:
        """
        Test similarity search functionality.
        
        Args:
            test_hadm_id: HADM_ID to use for similarity search
            limit: Number of similar patients to return
            
        Returns:
            List of similar patient records
        """
        print(f"Testing similarity search for HADM_ID {test_hadm_id}...")
        
        try:
            # Get the embedding for the test admission
            test_result = (
                self.weaviate_client
                .query
                .get("UTTreeEmbedding", ["hadm_id", "subject_id", "temporal_sequence"])
                .with_where({
                    "path": ["hadm_id"],
                    "operator": "Equal",
                    "valueInt": test_hadm_id
                })
                .with_additional(["vector"])
                .do()
            )
            
            if not test_result["data"]["Get"]["UTTreeEmbedding"]:
                print(f"No embedding found for HADM_ID {test_hadm_id}")
                return []
            
            # Get the vector
            test_vector = test_result["data"]["Get"]["UTTreeEmbedding"][0]["_additional"]["vector"]
            
            # Perform similarity search
            similar_results = (
                self.weaviate_client
                .query
                .get("UTTreeEmbedding", ["hadm_id", "subject_id", "temporal_sequence", "sequence_length"])
                .with_near_vector({
                    "vector": test_vector
                })
                .with_limit(limit + 1)  # +1 to exclude self
                .with_additional(["distance"])
                .do()
            )
            
            # Filter out the test admission itself and return results
            similar_admissions = []
            for result in similar_results["data"]["Get"]["UTTreeEmbedding"]:
                if result["hadm_id"] != test_hadm_id:
                    similar_admissions.append({
                        "hadm_id": result["hadm_id"],
                        "subject_id": result["subject_id"],
                        "distance": result["_additional"]["distance"],
                        "sequence_length": result["sequence_length"]
                    })
                    
            return similar_admissions[:limit]
            
        except Exception as e:
            print(f"Error in similarity search test: {e}")
            return []
    
    def process_and_store_all(self, results: List[Tuple[int, str, Optional[List[float]]]]):
        """
        Complete processing pipeline: schema creation, storage, and linking.
        
        Args:
            results: List of tuples (hadm_id, sequence, embedding)
        """
        print("Starting complete vector storage and linking pipeline...")
        
        # Step 1: Create schema
        self.create_uttree_schema()
        
        # Step 2: Store embeddings in Weaviate
        hadm_id_to_uuid = self.store_embeddings_in_weaviate(results)
        
        # Step 3: Link Neo4j admissions to vectors
        self.link_admissions_to_vectors(hadm_id_to_uuid)
        
        # Step 4: Set up similarity search
        self.create_vector_similarity_index()
        
        # Step 5: Test similarity search with first available admission
        if hadm_id_to_uuid:
            test_hadm_id = list(hadm_id_to_uuid.keys())[0]
            similar_patients = self.test_similarity_search(test_hadm_id, limit=3)
            
            print(f"\nSimilarity search test for HADM_ID {test_hadm_id}:")
            for i, patient in enumerate(similar_patients, 1):
                print(f"{i}. HADM_ID: {patient['hadm_id']}, Distance: {patient['distance']:.4f}")
        
        print("Vector storage and linking pipeline completed!")
    
    def close_connections(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        print("Database connections closed")


def main():
    """Main execution function for testing."""
    # This would normally receive data from the embedding processing module
    from data_preprocessing import UTTreeDataPreprocessor
    from nlp_processing import UTTreeNLPProcessor
    from tree_embedding import UTTreeEmbeddingProcessor
    
    try:
        # Initialize all processors
        preprocessor = UTTreeDataPreprocessor()
        nlp_processor = UTTreeNLPProcessor()
        embedding_processor = UTTreeEmbeddingProcessor()
        vector_storage = UTTreeVectorStorage()
        
        # Execute pipeline
        selected_patients, structured_data = preprocessor.process_all(min_notes=10, sample_size=3)
        integrated_data = nlp_processor.process_all(selected_patients, structured_data)
        embedding_results = embedding_processor.process_all_admissions(integrated_data)
        
        # Store in vector database and link to Neo4j
        vector_storage.process_and_store_all(embedding_results)
        
        print(f"\nComplete UTTree V2 Pipeline Summary:")
        print(f"Selected patients: {len(selected_patients)}")
        print(f"Processed admissions: {len(integrated_data)}")
        
        successful_embeddings = sum(1 for _, _, emb in embedding_results if emb is not None)
        print(f"Generated embeddings: {successful_embeddings}")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
    finally:
        # Always close connections
        if 'vector_storage' in locals():
            vector_storage.close_connections()


if __name__ == "__main__":
    main()