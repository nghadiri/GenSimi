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

def process_merged_drug_lab_csv(file_path):
    # 1. Read the merged_drug_lab.csv file
    df = pd.read_csv(file_path)

    # Convert Timestame_id to datetime
    df['Timestame_id'] = pd.to_datetime(df['Timestame_id'])

    # Group by HADM_ID
    grouped = df.groupby('HADM_ID')

    results = {}

    for hadm_id, group in grouped:
        # Sort by Timestame_id
        group = group.sort_values('Timestame_id')

        # Initialize the structured_df
        structured_df = pd.DataFrame(columns=['Time', 'TemporalEventType', 'Event', 'Value'])

        # Create a dictionary to map dates to sequential time values
        date_to_time = defaultdict(int)
        for i, date in enumerate(group['Timestame_id'].unique()):
            date_to_time[date] = i + 1

        # Process each row in the group
        new_rows = []
        for _, row in group.iterrows():
            new_row = {
                'Time': date_to_time[row['Timestame_id']],
                'TemporalEventType': row['TemporalEventType'],
            }

            if row['entity'] == 'Drug' and pd.notna(row['value']):
                new_row['Event'] = 'MainDrug'
                new_row['Value'] = row['value']
                new_rows.append(new_row)
            elif row['value'] == 'abnormal':
                new_row['Event'] = row['entity']
                new_row['Value'] = row['value']
                new_rows.append(new_row)

        # Concatenate new rows to the structured_df
        if new_rows:
            structured_df = pd.concat([structured_df, pd.DataFrame(new_rows)], ignore_index=True)

        results[hadm_id] = structured_df

    return results

# Usage
result = process_merged_drug_lab_csv(inputdir+'merged_drug_lab.csv')

# Print the result for each HADM_ID
for hadm_id, df in result.items():
    print(f"HADM_ID: {hadm_id}")
    df.to_csv(targetdir+f'{hadm_id}-st.csv', index=False)
    #print(df)
    print("\n")