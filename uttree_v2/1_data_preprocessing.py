"""
UTTree V2 - Data Preprocessing Module

Optimized data preprocessing pipeline that combines patient selection, sampling,
and structured data processing into a single streamlined module.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Key Improvements in V2:
- Eliminates intermediate CSV storage where possible
- Combines multiple preprocessing steps
- Direct in-memory processing
- Optimized for modern embedding pipeline

Processing Steps:
1. Patient Selection and Filtering
2. Structured Data Processing (Prescriptions + Labs)
3. Data Quality Assessment
4. Memory-Efficient Quadruple Generation

Output: In-memory structured data ready for NLP processing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import os
import sys
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.config import load_app_settings

class UTTreeDataPreprocessor:
    def __init__(self):
        self.settings = load_app_settings()
        self.input_dir = self.settings['directories']['input_dir']
        self.def_dir = self.settings['directories']['def_dir']
        
    def load_and_filter_patients(self, min_notes: int = 10, sample_size: Optional[int] = None) -> List[int]:
        """
        Load admissions and notes, filter patients with sufficient documentation.
        
        Args:
            min_notes: Minimum number of clinical notes required per patient
            sample_size: Optional sample size for testing (None = all patients)
            
        Returns:
            List of selected subject IDs
        """
        print("Loading admissions and notes data...")
        
        # Load core data
        admissions_df = pd.read_csv(os.path.join(self.input_dir, 'ADMISSIONS.csv'))
        notes_df = pd.read_csv(os.path.join(self.input_dir, 'NOTEEVENTS.csv'))
        
        # Filter patients with sufficient clinical documentation
        notes_per_patient = notes_df.groupby('SUBJECT_ID')['ROW_ID'].count()
        qualified_patients = notes_per_patient[notes_per_patient >= min_notes].index.tolist()
        
        # Apply sampling if requested
        if sample_size and sample_size < len(qualified_patients):
            qualified_patients = np.random.choice(qualified_patients, size=sample_size, replace=False)
            
        print(f"Selected {len(qualified_patients)} patients with >={min_notes} notes")
        return qualified_patients
    
    def process_prescriptions(self, selected_patients: List[int]) -> pd.DataFrame:
        """
        Process prescription data into temporal quadruple format.
        
        Args:
            selected_patients: List of patient IDs to process
            
        Returns:
            DataFrame with prescription quadruples
        """
        print("Processing prescription data...")
        
        prescriptions_df = pd.read_csv(os.path.join(self.input_dir, 'PRESCRIPTIONS.csv'))
        prescriptions_df = prescriptions_df[prescriptions_df['SUBJECT_ID'].isin(selected_patients)]
        
        prescriptions_df.columns = prescriptions_df.columns.str.lower()
        prescriptions_df = prescriptions_df[['subject_id', 'hadm_id', 'startdate', 'enddate', 'drug_name_generic']]
        
        # Convert dates
        prescriptions_df['startdate'] = pd.to_datetime(prescriptions_df['startdate']).dt.date
        prescriptions_df['enddate'] = pd.to_datetime(prescriptions_df['enddate']).dt.date
        
        # Generate daily drug records
        drug_quadruples = []
        for _, row in prescriptions_df.iterrows():
            try:
                start_date = pd.to_datetime(row['startdate'])
                end_date = pd.to_datetime(row['enddate'])
                
                # Create daily records for drug administration period
                for day in pd.date_range(start_date, end_date, inclusive='both'):
                    drug_quadruples.append({
                        'subject_id': row['subject_id'],
                        'hadm_id': row['hadm_id'],
                        'timestamp': day.date(),
                        'temporal_event_type': 'RealTime',
                        'event': 'MainDrug',
                        'value': row['drug_name_generic']
                    })
            except Exception as e:
                continue
                
        return pd.DataFrame(drug_quadruples)
    
    def process_lab_events(self, selected_patients: List[int]) -> pd.DataFrame:
        """
        Process laboratory events into temporal quadruple format.
        
        Args:
            selected_patients: List of patient IDs to process
            
        Returns:
            DataFrame with lab event quadruples
        """
        print("Processing laboratory data...")
        
        # Load lab events and definitions
        lab_events_df = pd.read_csv(os.path.join(self.input_dir, 'LABEVENTS.csv'))
        lab_items_df = pd.read_csv(os.path.join(self.def_dir, 'D_LABITEMS.csv'))
        
        # Filter for selected patients
        lab_events_df = lab_events_df[lab_events_df['SUBJECT_ID'].isin(selected_patients)]
        
        lab_events_df.columns = lab_events_df.columns.str.lower()
        lab_items_df.columns = lab_items_df.columns.str.lower()
        
        # Handle missing HADM_IDs
        lab_events_df['hadm_id'] = lab_events_df['hadm_id'].fillna(-1).astype(int)
        
        # Merge with lab item definitions
        lab_events_df = lab_events_df.merge(lab_items_df, on='itemid', how='left')
        lab_events_df = lab_events_df.fillna("normal")
        
        # Convert to quadruple format
        lab_quadruples = []
        for _, row in lab_events_df.iterrows():
            lab_quadruples.append({
                'subject_id': row['subject_id'],
                'hadm_id': row['hadm_id'],
                'timestamp': pd.to_datetime(row['charttime']).date(),
                'temporal_event_type': 'RealTime',
                'event': row['label'],
                'value': row['flag']
            })
            
        return pd.DataFrame(lab_quadruples)
    
    def combine_structured_data(self, drug_data: pd.DataFrame, lab_data: pd.DataFrame) -> pd.DataFrame:
        """
        Combine drug and lab data into unified structured dataset.
        
        Args:
            drug_data: Processed prescription quadruples
            lab_data: Processed lab event quadruples
            
        Returns:
            Combined structured data DataFrame
        """
        print("Combining structured data...")
        
        # Combine datasets
        structured_data = pd.concat([drug_data, lab_data], ignore_index=True)
        
        # Sort by patient and timestamp
        structured_data = structured_data.sort_values(['subject_id', 'hadm_id', 'timestamp'])
        
        # Filter for clinically relevant events
        # Keep drugs and abnormal lab values
        filtered_data = structured_data[
            (structured_data['event'] == 'MainDrug') |
            (structured_data['value'] == 'abnormal')
        ]
        
        print(f"Generated {len(filtered_data)} structured data quadruples")
        return filtered_data
    
    def process_all(self, min_notes: int = 10, sample_size: Optional[int] = None) -> Tuple[List[int], pd.DataFrame]:
        """
        Execute complete data preprocessing pipeline.
        
        Args:
            min_notes: Minimum notes per patient
            sample_size: Optional sample size for testing
            
        Returns:
            Tuple of (selected_patients, structured_data)
        """
        print("Starting UTTree V2 data preprocessing...")
        
        # Step 1: Patient selection
        selected_patients = self.load_and_filter_patients(min_notes, sample_size)
        
        # Step 2: Process structured data
        drug_data = self.process_prescriptions(selected_patients)
        lab_data = self.process_lab_events(selected_patients)
        
        # Step 3: Combine structured data
        structured_data = self.combine_structured_data(drug_data, lab_data)
        
        print("Data preprocessing completed successfully!")
        return selected_patients, structured_data


def main():
    """Main execution function for testing."""
    preprocessor = UTTreeDataPreprocessor()
    
    # Process with sample for testing
    selected_patients, structured_data = preprocessor.process_all(
        min_notes=10,
        sample_size=10  # Small sample for testing
    )
    
    print(f"\nProcessing Summary:")
    print(f"Selected patients: {len(selected_patients)}")
    print(f"Structured data records: {len(structured_data)}")
    print(f"Unique admissions: {structured_data['hadm_id'].nunique()}")
    
    # Display sample data
    print("\nSample structured data:")
    print(structured_data.head())


if __name__ == "__main__":
    main()