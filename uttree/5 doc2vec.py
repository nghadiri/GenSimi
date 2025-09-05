"""
Document Representation Module - UTTree Doc2Vec Integration

This module implements the final step of the UTTree pipeline by loading
generated temporal tree sequences into Neo4j for GraphRAG integration.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Document Representation Process:

1. Tree Sequence Integration:
   - Reads temporal tree sequences from {HADM_ID}-merged.txt files
   - Matches sequences with existing admission nodes in Neo4j
   - Updates admission nodes with temporal_tree_string properties

2. Doc2Vec Preparation:
   - Sequences serve as input documents for Doc2Vec algorithm
   - Each patient admission becomes a "document" with medical event sequences
   - Captures co-occurrence patterns and temporal relationships

3. Neo4j Integration:
   - Links temporal sequences to existing admission data
   - Enables GraphRAG queries to utilize both graph structure and temporal patterns
   - Supports hybrid retrieval combining graph relationships and semantic similarity

According to the methodology, Doc2Vec processes these sequences using:
- Distributed Memory Model (PV-DM): Predicts target words from context
- Hierarchical softmax optimization
- Fixed-length vector outputs regardless of input sequence length

The temporal tree strings contain rich compound sequences that demonstrate
medical event co-occurrences within time windows, enhanced by the
Weisfeiler-Lehman relabeling process.

This integration enables the GraphRAG system to leverage both:
- Structured medical knowledge graphs (Neo4j relationships)
- Temporal patient similarity patterns (UTTree sequences)

Input: {HADM_ID}-merged.txt files containing temporal tree sequences
Output: Neo4j admission nodes enhanced with temporal_tree_string properties
"""

from neo4j import GraphDatabase
import os
from typing import Dict, Set

# Load settings (using your existing config setup)
from util.config import load_app_settings
settings = load_app_settings()

uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
merged_dir = os.path.join(settings['directories']['input_dir'], "proc", "merged")

class StringLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_existing_admission_ids(self) -> Set[str]:
        """Get all existing admission IDs from Neo4j."""
        with self.driver.session() as session:
            result = session.run("MATCH (a:Admission) RETURN a.hadm_id as hadm_id")
            return set(str(record["hadm_id"]) for record in result)

    def update_admission_strings(self, admission_strings: Dict[str, str]):
        with self.driver.session() as session:
            cnt = 0
            for hadm_id, temporal_string in admission_strings.items():
                session.execute_write(self._update_admission_string, hadm_id, temporal_string)
                cnt += 1
                print(f"Updated admission {hadm_id} ({cnt}/{len(admission_strings)})")

    @staticmethod
    def _update_admission_string(tx, hadm_id: str, temporal_string: str):
        query = """
        MATCH (a:Admission {hadm_id: $hadm_id})
        SET a.temporal_tree_string = $temporal_string
        """
        tx.run(query,
               hadm_id=hadm_id,
               temporal_string=temporal_string)

def read_admission_strings(merged_dir: str, existing_hadm_ids: Set[str]) -> Dict[str, str]:
    """Read strings from text files for existing admissions."""
    admission_strings = {}
    
    # List all merged files
    try:
        files = os.listdir(merged_dir)
    except Exception as e:
        print(f"Error reading directory {merged_dir}: {str(e)}")
        return admission_strings

    # Process each file
    for filename in files:
        if not filename.endswith('-merged.txt'):
            continue
            
        # Extract admission ID from filename (e.g., "100422-merged.txt" -> "100422")
        hadm_id = filename.split('-')[0]
        
        if hadm_id in existing_hadm_ids:
            try:
                with open(os.path.join(merged_dir, filename), 'r', encoding='utf-8') as f:
                    temporal_string = f.read().strip()
                    admission_strings[hadm_id] = temporal_string
            except Exception as e:
                print(f"Error reading file {filename}: {str(e)}")
                continue
    
    return admission_strings

if __name__ == "__main__":
    # Initialize loader
    loader = StringLoader(uri=uri, user=user, password=password)

    try:
        # 1. Get existing admission IDs from Neo4j
        print("Getting existing admission IDs from Neo4j...")
        existing_hadm_ids = loader.get_existing_admission_ids()
        print(f"Found {len(existing_hadm_ids)} existing admissions")
        print("Sample admission IDs:", list(existing_hadm_ids)[:5])

        # 2. Read strings from files for existing admissions
        print(f"\nReading strings from {merged_dir}...")
        admission_strings = read_admission_strings(merged_dir, existing_hadm_ids)
        print(f"Read {len(admission_strings)} strings for existing admissions")

        # Print stats about matches
        print("\nMatching Statistics:")
        print(f"Total existing admissions: {len(existing_hadm_ids)}")
        print(f"Admissions with strings found: {len(admission_strings)}")
        missing_admissions = existing_hadm_ids - set(admission_strings.keys())
        print(f"Admissions without strings: {len(missing_admissions)}")
        
        if missing_admissions:
            print("\nSample of admissions without strings:")
            print(list(missing_admissions)[:5])

        if admission_strings:
            print("\nSample of found strings (first 100 chars):")
            sample_items = list(admission_strings.items())[:3]
            for hadm_id, string in sample_items:
                print(f"HADM_ID: {hadm_id}, String: {string[:100]}...")

            # 3. Update admissions in Neo4j
            print("\nUpdating admissions in Neo4j...")
            loader.update_admission_strings(admission_strings)
            print("\nString loading completed successfully!")
        else:
            print("\nNo strings found for existing admissions!")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
    finally:
        loader.close()