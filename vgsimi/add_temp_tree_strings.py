from neo4j import GraphDatabase
import os
from typing import Dict, Set
import sys
from openai import OpenAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load settings (using your existing config setup)
from util.config import load_app_settings
settings = load_app_settings()

uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
merged_dir = os.path.join(settings['directories']['input_dir'], "proc", "merged")

class StringLoader:
    def __init__(self, uri: str, user: str, password: str, openai_api_key=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.openai_client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))

    def close(self):
        self.driver.close()

    def generate_embedding_s(self, text: str) -> list:
        """Generate embedding using OpenAI's API"""
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def generate_embedding(self, text: str) -> list:
        """Generate embedding using OpenAI's API with chunking for long texts"""
        if not text or not text.strip():
            raise ValueError("Empty text provided")
            
        print(f"Input text length: {len(text)} characters")
        
        # Instead of sentence splitting, we'll chunk by character count with some buffer
        # Assuming average of 3 characters per token, we'll use 24000 characters as max chunk size
        # (8192 token limit * 3 chars per token = ~24000, using 20000 to be safe)
        MAX_CHUNK_SIZE = 20000
        
        # Split text into chunks
        chunks = []
        for i in range(0, len(text), MAX_CHUNK_SIZE):
            chunk = text[i:i + MAX_CHUNK_SIZE]
            # Try to break at an underscore if possible
            if i + MAX_CHUNK_SIZE < len(text):
                # Find the last underscore in this chunk
                last_underscore = chunk.rfind('_')
                if last_underscore != -1:
                    # Split at the underscore
                    chunk = chunk[:last_underscore]
                    # Adjust the next iteration start point
                    i = i + last_underscore
            chunks.append(chunk)
        
        print(f"Split into {len(chunks)} chunks")
        
        # Generate embeddings for each chunk
        all_embeddings = []
        for i, chunk in enumerate(chunks):
            try:
                if not chunk.strip():
                    print(f"Skipping empty chunk {i}")
                    continue
                    
                print(f"Processing chunk {i+1}/{len(chunks)} of length {len(chunk)} chars")
                print(f"Sample of chunk: {chunk[:100]}...")
                
                response = self.openai_client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-small"
                )
                all_embeddings.append(response.data[0].embedding)
                print(f"Successfully embedded chunk {i+1}")
                
            except Exception as e:
                print(f"Error generating embedding for chunk {i+1}: {str(e)}")
                print(f"Problematic chunk: {chunk[:200]}...")
                continue
        
        if not all_embeddings:
            print("ERROR: No valid embeddings were generated")
            print("First 200 chars of original text:", text[:200])
            raise ValueError("Could not generate any valid embeddings for the text")
        
        # Calculate the average embedding
        avg_embedding = [
            sum(values) / len(values)
            for values in zip(*all_embeddings)
        ]
        
        print(f"Successfully generated average embedding from {len(all_embeddings)} chunks")
        return avg_embedding

    def update_admission_strings_and_vectors(self, admission_strings: Dict[str, str]):
        """Update both strings and their embeddings"""
        with self.driver.session() as session:
            cnt = 0
            for hadm_id, temporal_string in admission_strings.items():
                try:
                    print(f"\nProcessing admission {hadm_id}")
                    
                    # First update the string
                    session.execute_write(self._update_admission_string, hadm_id, temporal_string)
                    print(f"Updated string for admission {hadm_id}")
                    
                    # Then generate and update the embedding
                    vector = self.generate_embedding(temporal_string)
                    session.execute_write(self._update_admission_vector, hadm_id, vector)
                    
                    cnt += 1
                    print(f"Successfully updated admission {hadm_id} with string and vector ({cnt}/{len(admission_strings)})")
                    
                except Exception as e:
                    print(f"ERROR processing admission {hadm_id}: {str(e)}")
                    print(f"First 200 chars of problematic text: {temporal_string[:200]}")
                    continue

    @staticmethod
    def _update_admission_vector(tx, hadm_id: str, vector: list):
        """Store the embedding vector in Neo4j"""
        query = """
        MATCH (a:Admission {hadm_id: toInteger($hadm_id)})
        SET a.vector = $vector
        RETURN a.vector as new_vector
        """
        result = tx.run(query,
                       hadm_id=hadm_id,
                       vector=vector)
        return result.single()["new_vector"]

    def update_admission_strings_and_vectors(self, admission_strings: Dict[str, str]):
        """Update both strings and their embeddings"""
        with self.driver.session() as session:
            cnt = 0
            for hadm_id, temporal_string in admission_strings.items():
                # First update the string
                session.execute_write(self._update_admission_string, hadm_id, temporal_string)
                
                # Then generate and update the embedding
                vector = self.generate_embedding(temporal_string)
                session.execute_write(self._update_admission_vector, hadm_id, vector)
                
                cnt += 1
                print(f"Updated admission {hadm_id} with string and vector ({cnt}/{len(admission_strings)})")


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
        MATCH (a:Admission {hadm_id: toInteger($hadm_id)})
        SET a.temporal_tree_string = $temporal_string
        RETURN a.temporal_tree_string as new_value
        """
        print(hadm_id, temporal_string[:30])
        result = tx.run(query,
            hadm_id=hadm_id,
            temporal_string=temporal_string)
        # Optional: verify the update
        print("New value:", result.single()["new_value"])

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
    # Initialize loader with OpenAI API key
    loader = StringLoader(
        uri=uri, 
        user=user, 
        password=password
        #openai_api_key='your-openai-api-key'  # or set OPENAI_API_KEY environment variable
    )

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
            print("\nUpdating admissions with strings and vectors in Neo4j...")
            loader.update_admission_strings_and_vectors(admission_strings)  # Use new method instead
            print("\nString and vector loading completed successfully!")
        else:
            print("\nNo strings found for existing admissions!")


    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
    finally:
        loader.close()