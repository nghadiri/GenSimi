import pandas as pd
from collections import defaultdict

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']
targetdir=settings['directories']['target_dir']
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
