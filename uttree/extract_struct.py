import pandas as pd
import datetime as dt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict
from util.config import load_app_settings

def load_settings() -> Dict:
    settings = load_app_settings()
    return {
        'input_dir': settings['directories']['input_dir'],
        'target_dir': settings['directories']['input_dir'],
        'def_dir': settings['directories']['def_dir']
    }

def load_and_preprocess_prescription_data(input_dir: str) -> pd.DataFrame:
    data = pd.read_csv(f"{input_dir}PRESCRIPTIONS.csv")
    data.columns = data.columns.str.lower()
    data = data[['subject_id', 'hadm_id', 'startdate', 'enddate', 'drug_type', 'drug_name_generic']]
    data['startdate'] = pd.to_datetime(data['startdate']).dt.date
    data['enddate'] = pd.to_datetime(data['enddate']).dt.date
    return data

def create_drug_stage_df(data: pd.DataFrame) -> pd.DataFrame:
    stage_ls_drug = []
    for _, row in data.iterrows():
        try:
            sdate = pd.to_datetime(row['startdate'])
            edate = pd.to_datetime(row['enddate'])
            for day in pd.date_range(sdate, edate, inclusive='both'):
                stage_ls_drug.append([
                    row['subject_id'],
                    row['hadm_id'],
                    str(day.date()),
                    'RealTime',
                    'Drug',
                    row['drug_name_generic']
                ])
        except Exception as e:
            print(f"Error processing row: {e}")
    
    return pd.DataFrame(stage_ls_drug, columns=['Subject_id', 'HADM_ID', 'Timestame_id', 'TemporalEventType', 'entity', 'value'])

def load_and_preprocess_lab_data(input_dir: str, def_dir: str) -> pd.DataFrame:
    df_lab = pd.read_csv(f"{input_dir}LABEVENTS.csv")
    df_lab_items = pd.read_csv(f"{def_dir}D_LABITEMS.csv")
    
    df_lab.columns = df_lab.columns.str.lower()
    df_lab_items.columns = df_lab_items.columns.str.lower()
    
    df_lab['hadm_id'] = df_lab['hadm_id'].fillna(-1).astype(int)
    
    df_merged = pd.merge(df_lab, df_lab_items, how='left', on=['itemid'])
    df_merged = df_merged.fillna("normal")
    
    return df_merged

def create_lab_stage_df(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        'Subject_id': df.subject_id,
        'HADM_ID': df.hadm_id,
        'Timestame_id': pd.to_datetime(df['charttime']).dt.date,
        'TemporalEventType': 'RealTime',
        'entity': df.label,
        'value': df.flag
    })

def main():
    settings = load_settings()
    
    # Process prescription data
    prescription_data = load_and_preprocess_prescription_data(settings['input_dir'])
    stage_df_drug = create_drug_stage_df(prescription_data)
    
    # Process lab data
    lab_data = load_and_preprocess_lab_data(settings['input_dir'], settings['def_dir'])
    stage_df_lab = create_lab_stage_df(lab_data)
    
    # Merge results
    result = pd.concat([stage_df_lab, stage_df_drug])
    
    # Save results
    result.to_csv(f"{settings['target_dir']}merged_drug_lab.csv", index=False)
    
    # Print statistics
    num_unique_subjects = result['Subject_id'].nunique()
    print(f"Number of unique subject ids: {num_unique_subjects}")

if __name__ == "__main__":
    main()