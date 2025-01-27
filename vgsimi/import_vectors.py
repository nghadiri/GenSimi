from neo4j import GraphDatabase
import pandas as pd
import numpy as np
from typing import List, Dict
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

uri = settings['neo4j']['uri']
user = settings['neo4j']['user']
password = settings['neo4j']['password']

inputdir = settings['directories']['input_dir']
targetdir = settings['directories']['target_dir']

class Neo4jLoader:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def load_patients(self, patients_df: pd.DataFrame):
        with self.driver.session() as session:
            for _, row in patients_df.iterrows():
                session.execute_write(self._create_patient, dict(row))

    def load_admissions(self, admissions_df: pd.DataFrame, vectors_df: pd.DataFrame):
        # Only keep the vector columns and admission ID
        vectors_df = vectors_df[['admission_id'] + [col for col in vectors_df.columns if col.startswith('f')]]
        
        with self.driver.session() as session:
            for _, row in admissions_df.iterrows():
                # Get the vector for this admission
                admission_vector = vectors_df[vectors_df['admission_id'] == row['hadm_id']]
                vector = admission_vector.iloc[0][vectors_df.columns[1:]].values.tolist() if not admission_vector.empty else []
                
                session.execute_write(self._create_admission, dict(row), vector)

    def load_lab_events(self, lab_events_df: pd.DataFrame):
        with self.driver.session() as session:
            for _, row in lab_events_df.iterrows():
                lab_data = dict(row)
                lab_data['id'] = f"LAB_{lab_data['row_id']}"
                session.execute_write(self._create_lab_event, lab_data)

    def load_prescriptions(self, prescriptions_df: pd.DataFrame):
        with self.driver.session() as session:
            for _, row in prescriptions_df.iterrows():
                prescription_data = dict(row)
                prescription_data['id'] = f"PRESCRIPTION_{prescription_data['row_id']}"
                session.execute_write(self._create_prescription, prescription_data)

    @staticmethod
    def _create_patient(tx, patient_data):
        query = """
        MERGE (p:Patient {subject_id: $subject_id})
        SET p += $patient_data
        """
        tx.run(query, subject_id=patient_data['subject_id'], patient_data=patient_data)

    @staticmethod
    def _create_admission(tx, admission_data, vector):
        query = """
        MATCH (p:Patient {subject_id: $subject_id})
        MERGE (a:Admission {hadm_id: $hadm_id})
        SET a = $admission_data
        SET a.vector = $vector
        MERGE (p)-[:HAS_ADMISSION]->(a)
        """
        tx.run(query, 
               subject_id=admission_data['subject_id'],
               hadm_id=admission_data['hadm_id'],
               admission_data=admission_data,
               vector=vector)

    @staticmethod
    def _create_lab_event(tx, lab_data):
        query = """
        MATCH (a:Admission {hadm_id: $hadm_id})
        CREATE (l:LabEvent {id: $id})
        SET l += $lab_data
        WITH a, l
        CREATE (a)-[r:HAS_LAB]->(l)
        """
        tx.run(query,
               hadm_id=lab_data['hadm_id'],
               id=lab_data['id'],
               lab_data=lab_data)

    @staticmethod
    def _create_prescription(tx, prescription_data):
        query = """
        MATCH (a:Admission {hadm_id: $hadm_id})
        CREATE (p:Prescription {id: $id})
        SET p += $prescription_data
        WITH a, p
        CREATE (a)-[r:HAS_PRESCRIPTION]->(p)
        """
        tx.run(query,
               hadm_id=prescription_data['hadm_id'],
               id=prescription_data['id'],
               prescription_data=prescription_data)

def filter_data_for_admissions(admissions_df, patients_df, lab_events_df, prescriptions_df, vectors_df, n_samples=50):
    # Randomly select n admissions
    sampled_admissions = admissions_df.sample(n=n_samples, random_state=42)
    
    # Get related data
    selected_hadm_ids = sampled_admissions['hadm_id'].tolist()
    selected_subject_ids = sampled_admissions['subject_id'].tolist()
    
    # Filter related data
    filtered_patients = patients_df[patients_df['subject_id'].isin(selected_subject_ids)]
    filtered_labs = lab_events_df[lab_events_df['hadm_id'].isin(selected_hadm_ids)]
    filtered_prescriptions = prescriptions_df[prescriptions_df['hadm_id'].isin(selected_hadm_ids)]
    filtered_vectors = vectors_df[vectors_df['admission_id'].isin(selected_hadm_ids)]
    
    return filtered_patients, sampled_admissions, filtered_labs, filtered_prescriptions, filtered_vectors

# Usage example:
if __name__ == "__main__":
    # Initialize connection
    loader = Neo4jLoader(
        uri=uri,
        user=user,
        password=password
    )

    try:
        # Load data with lowercase column names
        patients_df = pd.read_csv(os.path.join(inputdir, "patients.csv"))
        patients_df.columns = patients_df.columns.str.lower()

        admissions_df = pd.read_csv(os.path.join(inputdir, "admissions.csv"))
        admissions_df.columns = admissions_df.columns.str.lower()

        lab_events_df = pd.read_csv(os.path.join(inputdir, "labevents.csv"))
        lab_events_df.columns = lab_events_df.columns.str.lower()

        prescriptions_df = pd.read_csv(os.path.join(inputdir, "prescriptions.csv"))
        prescriptions_df.columns = prescriptions_df.columns.str.lower()

        vectors_df = pd.read_csv(os.path.join(inputdir, "embedded_vectors.csv"))
        vectors_df.columns = vectors_df.columns.str.lower()
        # Rename admission_Id to admission_id for consistency
        if 'admission_id' not in vectors_df.columns and 'admission_id' in vectors_df.columns:
            vectors_df = vectors_df.rename(columns={'admission_id': 'admission_id'})

        # Filter data for 50 random admissions
        filtered_patients, filtered_admissions, filtered_labs, filtered_prescriptions, filtered_vectors = \
            filter_data_for_admissions(admissions_df, patients_df, lab_events_df, prescriptions_df, vectors_df)

        # Load filtered data
        print("Loading patients...")
        loader.load_patients(filtered_patients)
        print("Loading admissions...")
        loader.load_admissions(filtered_admissions, filtered_vectors)
        print("Loading lab events...")
        loader.load_lab_events(filtered_labs)
        print("Loading prescriptions...")
        loader.load_prescriptions(filtered_prescriptions)

        print("Data loading completed successfully!")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise e
    finally:
        loader.close()