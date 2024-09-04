import pandas as pd
from collections import defaultdict

import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']
targetdir=settings['directories']['target_dir']+"proc\\"
ddir=settings['directories']['def_dir']

def process_cui_csv(file_path):
    # 1. Read the cui.csv file
    df = pd.read_csv(file_path)

    # Convert CHARTDATE to datetime
    df['CHARTDATE'] = pd.to_datetime(df['CHARTDATE'])

    # Group by HADM_ID
    grouped = df.groupby('HADM_ID')

    results = {}

    for hadm_id, group in grouped:
        # Sort by CHARTDATE
        group = group.sort_values('CHARTDATE')

        # Initialize the unstructured_df
        unstructured_df = pd.DataFrame(columns=['Time', 'TemporalEventType', 'Event', 'Value'])

        # Create a dictionary to map dates to sequential time values
        date_to_time = defaultdict(int)
        for i, date in enumerate(group['CHARTDATE'].unique()):
            date_to_time[date] = i + 1

        # Process each row in the group
        new_rows = []
        for _, row in group.iterrows():
            if row['label'] == 'DISEASE':
                new_row = {
                    'Time': date_to_time[row['CHARTDATE']],
                    'TemporalEventType': 'Retro' if row['category_Inner'] == 'past_medical_history' else 'NewFinding',
                    'Event': 'DiseaseDisorderMention',
                    'Value': row['canonical_name']
                }
                new_rows.append(new_row)

        # Concatenate new rows to the unstructured_df
        if new_rows:
            unstructured_df = pd.concat([unstructured_df, pd.DataFrame(new_rows)], ignore_index=True)

        results[hadm_id] = unstructured_df

    return results

# Usage
#file_path = 'cui.csv'
result = process_cui_csv(inputdir+'cui.csv')

# Print the result for each HADM_ID
for hadm_id, df in result.items():
    print(f"HADM_ID: {hadm_id}")
    df.to_csv(targetdir+f'{hadm_id}-unst.csv', index=False)
    #print(df)
    print("\n")