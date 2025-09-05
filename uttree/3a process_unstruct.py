"""
Unstructured Data Processor - UTTree Quadruple Generation

This module processes extracted medical concepts from clinical notes (cui.csv)
and converts them into standardized quadruple format for temporal tree construction.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Processing Steps:
1. Groups extracted concepts by hospital admission (HADM_ID)
2. Creates temporal ordering based on chart dates
3. Assigns temporal event types based on clinical section:
   - 'Retro': Past medical history concepts (retrospective data)
   - 'NewFinding': Current visit disease findings (long-lasting effects)

4. Converts to Quadruple Format:
   - Time: Sequential time window (1, 2, 3, ...)
   - TemporalEventType: Retro or NewFinding
   - Event: 'DiseaseDisorderMention' for disease entities
   - Value: UMLS canonical name of the medical concept

Key Features:
- Filters for DISEASE label entities only
- Maps section categories to temporal event types
- Creates time-ordered sequences for each admission
- Outputs separate files for each admission's unstructured data

This module transforms raw NLP extraction results into the standardized
quadruple format required for temporal tree construction in the UTTree model.

Input: cui.csv (extracted medical concepts with UMLS mappings)
Output: {HADM_ID}-unst.csv files containing quadruple-formatted unstructured data
"""

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