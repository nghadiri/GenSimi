
"""
Structured Data Processing Module - UTTree Pipeline

This module processes structured EMR data (prescriptions and laboratory events) 
to create quadruple data structures for the UTTree methodology.

Based on the UTTree methodology from:
"A study into patient similarity through representation learning from medical records"
by Memarzadeh et al. (2022)

Structured Data Processing Steps:
1. Prescription Processing:
   - Extracts drug information with start/end dates
   - Creates daily drug administration records
   - Converts to quadruple format: {time, event_type, entity, value}
   - Assigns 'RealTime' temporal event type for short-term effects

2. Laboratory Events Processing:
   - Merges lab events with lab item definitions
   - Processes lab results and flags (normal/abnormal)
   - Creates temporal records for each lab test
   - Maps to quadruple format with 'RealTime' event type

3. Quadruple Data Structure:
   According to Table 2 in the methodology, each quadruple contains:
   - Time (t_i): Timestamp of clinical event registration
   - Temporal Event Type (y_i): Retrospective/NewFinding/RealTime
   - Event (e_i): Medical event type (disease, drug, lab, etc.)
   - Value (v_i): Medical event value

This harmonization enables combination of structured and unstructured data
in the tree construction phase of the UTTree model.

Input: PRESCRIPTIONS.csv, LABEVENTS.csv, D_LABITEMS.csv
Output: merged_drug_lab.csv containing harmonized quadruple structures
"""

import pandas as pd

from util.config import load_app_settings
settings = load_app_settings()

inputdir=settings['directories']['input_dir']
targetdir=settings['directories']['input_dir']
ddir=settings['directories']['def_dir']

data=pd.read_csv(inputdir+'PRESCRIPTIONS.csv')

data.columns = data.columns.str.lower()

data=data[['subject_id',	'hadm_id','startdate',	'enddate', 'drug_type', 'drug_name_generic']]

import datetime as dt
data['startdate']=pd.to_datetime(data['startdate']).dt.date
data['enddate']=pd.to_datetime(data['enddate']).dt.date

import pandas as pd

def create_drug_stage_df(data):
    """
    Creates a DataFrame representing drug stages within specified date ranges.

    Args:
        data (pd.DataFrame): DataFrame containing drug data with columns 'startdate', 'enddate', 'subject_id', 'hadm_id', and 'drug'.

    Returns:
        pd.DataFrame: DataFrame with columns 'Subject_id', 'HADM_ID', 'Timestame_id', 'TemporalEventType', 'entity', and 'value'.
    """

    Stage_ls_Drug = []
    for i in data.index:
        try:
            sdate = pd.to_datetime(data.loc[i, 'startdate'])
            edate = pd.to_datetime(data.loc[i, 'enddate'])
            v_SUBJECT_ID = data.loc[i, 'subject_id']
            v_HADM_ID = data.loc[i, 'hadm_id']
            v_DRUG = data.loc[i, 'drug_name_generic']
            v_DRUG_TYPE = 'Drug'

            # Efficiently create date range using pd.date_range
            for day in pd.date_range(sdate, edate, inclusive='both'):
                Stage_ls_Drug.append([v_SUBJECT_ID, v_HADM_ID, str(day.date()), 'RealTime', v_DRUG_TYPE, v_DRUG])
        except Exception as e:
            print(f"Error processing row {i}: {e}")

    return pd.DataFrame(Stage_ls_Drug, columns=['Subject_id', 'HADM_ID', 'Timestame_id', 'TemporalEventType', 'entity', 'value'])

# Example usage
Stage_ls_Drug = []
Stage_df_Drug = create_drug_stage_df(data.copy())  # Avoid modifying original data


from datetime import datetime
from datetime import date, timedelta
Stage_ls_Drug=[]
for c in range(len(data)):

    try:
        sdate=pd.to_datetime(data.iloc[c]['startdate'], infer_datetime_format=True)
        edate=pd.to_datetime(data.iloc[c]['enddate'], infer_datetime_format=True)
        v_SUBJECT_ID=data.iloc[c]['subject_id']
        v_HADM_ID=data.iloc[c]['hadm_id']
        v_DRUG=data.iloc[c]['drug_name_generic']
        #v_DRUG=data.iloc[c]['drug']
        v_DRUG_TYPE='Drug'#data.iloc[c]['drug_type']
        delta = edate - sdate       # as timedelta
        #print(c)
        i=0
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
            Stage_ls_Drug.append([v_SUBJECT_ID,v_HADM_ID,str(day.date()),'RealTime',v_DRUG_TYPE,v_DRUG])
    except:
        print(c,'Error')

Stage_df_Drug=pd.DataFrame(Stage_ls_Drug,columns=['Subject_id','HADM_ID','Timestame_id','TemporalEventType','entity','value'])

#Stage_df_Drug

"""**Lab**"""

df_lab=pd.read_csv(inputdir+"LABEVENTS.csv")

df_lab_Items=pd.read_csv(ddir+"D_LABITEMS.csv")

df_lab.columns = df_lab.columns.str.lower()
df_lab_Items.columns = df_lab_Items.columns.str.lower()

#data['hadm_id'].isna().sum()

#df_lab.tail()

df_lab['hadm_id'] = df_lab['hadm_id'].fillna(-1).astype(int)  # Replace NaN with -1

#df_lab[df_lab['hadm_id']==-1]

#df_lab.head()

# Assuming df_lab is your DataFrame containing lab data
num_nan_hadm_ids = df_lab['hadm_id'].isna().sum()
print("Number of NaN HADM_IDs in df_lab:", num_nan_hadm_ids)


df_lab=pd.merge(df_lab,df_lab_Items,how='left',on=['itemid'])
df_lab=df_lab.fillna("normal")
#df_lab.head()

Stage_df = pd.DataFrame(columns=['Subject_id','HADM_ID','Timestame_id','TemporalEventType','entity','value'])
Stage_df.Subject_id=df_lab.subject_id

Stage_df.HADM_ID=df_lab.hadm_id

Stage_df.Timestame_id=pd.to_datetime(df_lab['charttime']).dt.date
Stage_df['TemporalEventType']='RealTime'
Stage_df.entity=df_lab.label
Stage_df.value=df_lab.flag
Stage_df=Stage_df.reset_index()
Stage_df_lab = Stage_df.drop('index', axis=1)
#Stage_df_lab

"""**Merge**"""

Stage = [Stage_df_lab, Stage_df_Drug]
result = pd.concat(Stage)
#result

result.to_csv(targetdir + 'merged_drug_lab.csv', index=False)

nu=result['Subject_id'].nunique()
print("Number of unique subject ids:", nu)

