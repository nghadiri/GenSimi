"""
UTTree V2 - Tree Construction and Embedding Module

Modernized tree construction with mxbai-embed-large embeddings via Ollama,
replacing Doc2Vec with state-of-the-art embedding models.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Improvements in V2:
- mxbai-embed-large via Ollama for superior embeddings
- Environment-based configuration (.env)
- In-memory tree processing
- Direct embedding generation without intermediate storage

Processing Steps:
1. Temporal Tree Construction (4-level hierarchy)
2. Weisfeiler-Lehman Relabeling
3. BFS Traversal and Sequence Generation
4. Modern Embedding Generation via Ollama
"""

import pandas as pd
import numpy as np
import networkx as nx
import re
import requests
import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings

class UTTreeEmbeddingProcessor:
    def __init__(self):
        self.settings = load_app_settings()
        
        # Get Ollama configuration from environment
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'mxbai-embed-large')
        
        # Verify Ollama connection
        self._verify_ollama_connection()
        
    def _verify_ollama_connection(self):
        """Verify connection to Ollama server and model availability."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                if self.embedding_model in models:
                    print(f"Connected to Ollama server with {self.embedding_model} model")
                else:
                    print(f"Warning: {self.embedding_model} not found in available models: {models}")
            else:
                print(f"Warning: Could not connect to Ollama server at {self.ollama_url}")
        except Exception as e:
            print(f"Warning: Ollama connection check failed: {e}")
    
    def construct_temporal_tree(self, admission_data: pd.DataFrame) -> nx.DiGraph:
        """
        Construct temporal tree for a single admission following UTTree methodology.
        
        Args:
            admission_data: DataFrame with quadruple data for one admission
            
        Returns:
            NetworkX DiGraph representing the temporal tree
        """
        tree = nx.DiGraph()
        
        # Level 1: Root node (Patient ID)
        root = 'PID'
        tree.add_node(root)
        
        # Get unique time windows
        time_windows = sorted(admission_data['time_window'].unique())
        
        # Level 2: Time window nodes
        for time_window in time_windows:
            time_node = str(time_window)
            tree.add_node(time_node)
            tree.add_edge(root, time_node)
            
            # Level 3: Temporal event type nodes
            window_data = admission_data[admission_data['time_window'] == time_window]
            event_types = window_data['temporal_event_type'].unique()
            
            for event_type in event_types:
                event_type_node = f"{event_type}-{tree.number_of_nodes()}"
                tree.add_node(event_type_node, temporal_event_type=event_type)
                tree.add_edge(time_node, event_type_node)
                
                # Level 4: Medical event leaf nodes
                event_data = window_data[window_data['temporal_event_type'] == event_type]
                
                for _, row in event_data.iterrows():
                    leaf_node = f"{row['event']}-{tree.number_of_nodes()}"
                    tree.add_node(leaf_node, event=row['event'], value=row['value'])
                    tree.add_edge(event_type_node, leaf_node)
        
        return tree
    
    def apply_weisfeiler_lehman_relabeling(self, tree: nx.DiGraph, root: str) -> nx.DiGraph:
        """
        Apply Weisfeiler-Lehman relabeling algorithm to the temporal tree.
        
        Args:
            tree: NetworkX tree to relabel
            root: Root node identifier
            
        Returns:
            Relabeled tree
        """
        # Remove empty temporal event type nodes (no children)
        nodes_to_remove = []
        for node in tree.nodes():
            try:
                path_length = nx.shortest_path_length(tree, source=root, target=node)
                if path_length == 2 and tree.out_degree(node) == 0:
                    nodes_to_remove.append(node)
            except nx.NetworkXNoPath:
                continue
                
        for node in nodes_to_remove:
            tree.remove_node(node)
        
        # Level 4 → 3: Relabel temporal event type nodes
        level_3_nodes = []
        for node in tree.nodes():
            try:
                if nx.shortest_path_length(tree, source=root, target=node) == 2:
                    level_3_nodes.append(node)
            except nx.NetworkXNoPath:
                continue
        
        for node in level_3_nodes:
            # Get child node values
            children = list(tree.successors(node))
            new_label = ''
            
            for child in children:
                child_data = tree.nodes[child]
                if 'value' in child_data:
                    new_label += f"_{child_data['event']}_{child_data['value']}"
            
            # Relabel node
            if new_label:
                mapping = {node: new_label}
                tree = nx.relabel_nodes(tree, mapping)
        
        # Level 3 → 2: Relabel time window nodes
        level_2_nodes = []
        for node in tree.nodes():
            try:
                if nx.shortest_path_length(tree, source=root, target=node) == 1:
                    level_2_nodes.append(node)
            except nx.NetworkXNoPath:
                continue
        
        for node in level_2_nodes:
            # Get successor labels
            successors = list(tree.successors(node))
            new_label = ''
            
            for successor in successors:
                new_label += f"_{successor}"
            
            if new_label:
                mapping = {node: new_label}
                tree = nx.relabel_nodes(tree, mapping)
        
        # Level 2 → 1: Relabel root node
        successors = list(tree.successors(root))
        new_root_label = ''
        
        for successor in successors:
            new_root_label += f"_{successor}"
        
        if new_root_label:
            mapping = {root: new_root_label}
            tree = nx.relabel_nodes(tree, mapping)
            root = new_root_label
        
        return tree, root
    
    def generate_bfs_sequence(self, tree: nx.DiGraph, root: str) -> str:
        """
        Generate BFS traversal sequence from the relabeled tree.
        
        Args:
            tree: Relabeled temporal tree
            root: Root node identifier
            
        Returns:
            BFS sequence string for embedding
        """
        # Perform BFS traversal
        bfs_tree = nx.bfs_tree(tree, source=root)
        bfs_nodes = list(bfs_tree.nodes())
        
        # Clean up the sequence
        sequence = bfs_nodes[0] if bfs_nodes else ""
        
        # Remove node IDs and clean formatting
        cleaned_sequence = re.sub(r"(-[0-9]+)", "", sequence)  # Remove node IDs
        cleaned_sequence = re.sub(r"__+", "_", cleaned_sequence)  # Replace multiple underscores
        cleaned_sequence = cleaned_sequence.strip("_")  # Remove leading/trailing underscores
        
        return cleaned_sequence
    
    def get_embedding_from_ollama(self, text: str) -> Optional[List[float]]:
        """
        Get embedding vector from Ollama mxbai-embed-large model.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            url = f"{self.ollama_url}/api/embeddings"
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding')
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")\n                return None
                
        except Exception as e:
            print(f"Error getting embedding from Ollama: {e}")
            return None
    
    def process_admission_to_embedding(self, hadm_id: int, admission_data: pd.DataFrame) -> Tuple[int, str, Optional[List[float]]]:\n        """
        Process single admission through complete tree construction and embedding pipeline.
        
        Args:
            hadm_id: Hospital admission ID
            admission_data: Quadruple data for the admission
            
        Returns:
            Tuple of (hadm_id, sequence_string, embedding_vector)
        """
        try:
            # Step 1: Construct temporal tree
            tree = self.construct_temporal_tree(admission_data)
            
            # Step 2: Apply Weisfeiler-Lehman relabeling
            relabeled_tree, root = self.apply_weisfeiler_lehman_relabeling(tree, 'PID')
            
            # Step 3: Generate BFS sequence
            sequence = self.generate_bfs_sequence(relabeled_tree, root)
            
            # Step 4: Get embedding from Ollama
            embedding = self.get_embedding_from_ollama(sequence)
            
            return hadm_id, sequence, embedding
            
        except Exception as e:
            print(f"Error processing admission {hadm_id}: {e}")
            return hadm_id, "", None
    
    def process_all_admissions(self, integrated_data: Dict[int, pd.DataFrame]) -> List[Tuple[int, str, Optional[List[float]]]]:\n        """
        Process all admissions through tree construction and embedding pipeline.
        
        Args:
            integrated_data: Dictionary mapping hadm_id to admission quadruple data
            
        Returns:
            List of tuples (hadm_id, sequence, embedding)
        """
        print("Starting tree construction and embedding generation...")
        
        results = []
        total_admissions = len(integrated_data)
        
        for idx, (hadm_id, admission_data) in enumerate(integrated_data.items(), 1):
            print(f"Processing admission {idx}/{total_admissions}: {hadm_id}")
            
            result = self.process_admission_to_embedding(hadm_id, admission_data)
            results.append(result)
            
            # Progress update
            if idx % 10 == 0:
                successful = sum(1 for _, _, emb in results if emb is not None)
                print(f"Processed {idx} admissions, {successful} successful embeddings")
        
        successful_embeddings = sum(1 for _, _, emb in results if emb is not None)
        print(f"Tree construction and embedding completed: {successful_embeddings}/{total_admissions} successful")
        
        return results


def main():
    """Main execution function for testing."""
    # This would normally receive data from the NLP processing module
    from data_preprocessing import UTTreeDataPreprocessor
    from nlp_processing import UTTreeNLPProcessor
    
    # Initialize processors
    preprocessor = UTTreeDataPreprocessor()
    nlp_processor = UTTreeNLPProcessor()
    embedding_processor = UTTreeEmbeddingProcessor()
    
    # Get preprocessed and NLP-processed data
    selected_patients, structured_data = preprocessor.process_all(min_notes=10, sample_size=3)
    integrated_data = nlp_processor.process_all(selected_patients, structured_data)
    
    # Process through tree construction and embedding
    results = embedding_processor.process_all_admissions(integrated_data)
    
    print(f"\nEmbedding Processing Summary:")
    print(f"Total admissions processed: {len(results)}")
    
    successful_results = [(hadm_id, seq, emb) for hadm_id, seq, emb in results if emb is not None]
    print(f"Successful embeddings: {len(successful_results)}")
    
    # Display sample results
    if successful_results:
        hadm_id, sequence, embedding = successful_results[0]
        print(f"\nSample result for HADM_ID {hadm_id}:")
        print(f"Sequence: {sequence[:100]}...")
        print(f"Embedding dimensions: {len(embedding) if embedding else 0}")


if __name__ == "__main__":
    main()