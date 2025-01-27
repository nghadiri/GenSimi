from neo4j import GraphDatabase
import pandas as pd
import os
from typing import List
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load settings (using your existing config setup)
from util.config import load_app_settings
settings = load_app_settings()

uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']
inputdir = settings['directories']['input_dir']

class NoteLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_existing_admission_ids(self) -> List[str]:
        with self.driver.session() as session:
            result = session.run("MATCH (a:Admission) RETURN a.hadm_id as hadm_id")
            return [record["hadm_id"] for record in result]

    def load_note_events(self, notes_df: pd.DataFrame):
        with self.driver.session() as session:
            cnt = 0
            for _, row in notes_df.iterrows():
                note_data = dict(row)
                note_data['id'] = f"NOTE_{note_data['row_id']}"
                session.execute_write(self._create_note_event, note_data)
                cnt += 1
                if cnt % 100 == 0:  # Print progress every 100 notes
                    print(f"Processed {cnt} notes")

    @staticmethod
    def _create_note_event(tx, note_data):
        query = """
        MATCH (a:Admission {hadm_id: $hadm_id})
        CREATE (n:NoteEvent {id: $id})
        SET n += $note_data
        WITH a, n
        CREATE (a)-[r:HAS_NOTE]->(n)
        """
        tx.run(query,
               hadm_id=note_data['hadm_id'],
               id=note_data['id'],
               note_data=note_data)

if __name__ == "__main__":
    # Initialize loader
    loader = NoteLoader(uri=uri, user=user, password=password)

    try:
        # 1. Get existing admission IDs from Neo4j
        print("Getting existing admission IDs from Neo4j...")
        existing_hadm_ids = loader.get_existing_admission_ids()
        print(f"Found {len(existing_hadm_ids)} existing admissions")

        # 2. Load and filter notes
        print("Loading NOTEEVENTS...")
        notes_df = pd.read_csv(os.path.join(inputdir, "noteevents.csv"))
        notes_df.columns = notes_df.columns.str.lower()

        # Filter notes for existing admissions and text length > 50 words
        print("Filtering notes...")
        filtered_notes = notes_df[notes_df['hadm_id'].isin(existing_hadm_ids)].copy()
        filtered_notes['word_count'] = filtered_notes['text'].str.split().str.len()
        filtered_notes = filtered_notes[filtered_notes['word_count'] > 50]
        filtered_notes = filtered_notes.drop('word_count', axis=1)

        print(f"\nNote Statistics:")
        print(f"Total notes for existing admissions: {len(notes_df[notes_df['hadm_id'].isin(existing_hadm_ids)])}")
        print(f"Notes with >50 words: {len(filtered_notes)}")

        # 3. Load filtered notes into Neo4j
        print("\nLoading filtered notes into Neo4j...")
        loader.load_note_events(filtered_notes)

        print("\nNote loading completed successfully!")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
    finally:
        loader.close()