"""
Data Merger - UTTree Structured and Unstructured Integration

This module merges structured and unstructured quadruple data files to create
unified temporal datasets for each hospital admission in the UTTree pipeline.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Integration Process:
1. Identifies matching structured (-st.csv) and unstructured (-unst.csv) files
2. Combines both data types for each admission using pandas concatenation
3. Sorts merged data by temporal sequence (Time column)
4. Creates complete temporal records containing both:
   - Structured data: Drugs, lab results (RealTime events)
   - Unstructured data: Disease findings, medical history (Retro/NewFinding events)

Key Features:
- Handles cases where only one data type exists for an admission
- Maintains temporal ordering across combined data sources
- Creates unified input files for tree construction phase
- Organizes output in 'merged' subdirectory

This integration step is crucial for the UTTree methodology as it enables
the temporal tree to capture relationships between both structured medical
interventions and unstructured clinical observations within the same
time windows.

The merged data provides the foundation for creating four-level temporal
trees where medical events from different sources can be compared and
related through the Weisfeiler-Lehman relabeling process.

Input: {HADM_ID}-st.csv and {HADM_ID}-unst.csv files
Output: {HADM_ID}-merged.csv files containing integrated temporal data
"""

import pandas as pd
from collections import defaultdict

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']+"proc\\"
targetdir=settings['directories']['target_dir']+"proc\\"
ddir=settings['directories']['def_dir']

import os
import pandas as pd

def merge_csv_files(folder_path):
    # Get all csv files in the folder
    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    
    # Create a set of unique IDs from file names (without extensions and suffixes)
    unique_ids = set(f.split('-')[0] for f in files)
    
    for unique_id in unique_ids:
        # Construct the file names
        st_file = f"{unique_id}-st.csv"
        unst_file = f"{unique_id}-unst.csv"
        merged_file = f"{unique_id}-merged.csv"
        
        # Initialize an empty DataFrame
        df_merged = pd.DataFrame()
        
        # Check if both files exist and merge them
        if st_file in files and unst_file in files:
            df_st = pd.read_csv(os.path.join(folder_path, st_file))
            df_unst = pd.read_csv(os.path.join(folder_path, unst_file))
            df_merged = pd.concat([df_st, df_unst], ignore_index=True)
        elif st_file in files:
            df_merged = pd.read_csv(os.path.join(folder_path, st_file))
        elif unst_file in files:
            df_merged = pd.read_csv(os.path.join(folder_path, unst_file))
        
        # Sort the merged DataFrame by the 'Time' column
        if not df_merged.empty:
            df_merged = df_merged.sort_values(by='Time')
            df_merged.to_csv(os.path.join(folder_path, 'merged', merged_file), index=False)
            print(f"Created {merged_file}")

# Usage
folder_path = targetdir  # replace with the path to your folder
merge_csv_files(folder_path)
